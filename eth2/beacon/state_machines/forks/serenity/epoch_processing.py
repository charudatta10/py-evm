from typing import (
    Iterable,
    Sequence,
    Tuple,
)

from eth_utils import to_tuple

from eth2.beacon import helpers
from eth2._utils.numeric import (
    is_power_of_two,
)
from eth2._utils.tuple import (
    update_tuple_item,
)
from eth2.beacon.exceptions import (
    NoWinningRootError,
)
from eth2.beacon.committee_helpers import (
    get_crosslink_committees_at_slot,
    get_current_epoch_committee_count,
)
from eth2.beacon.configs import (
    BeaconConfig,
    CommitteeConfig,
)
from eth2.beacon.epoch_processing_helpers import (
    get_current_epoch_attestations,
    get_previous_epoch_attestations,
    get_winning_root,
    get_total_balance,
    get_epoch_boundary_attesting_balances,
)
from eth2.beacon.helpers import (
    get_active_validator_indices,
    get_effective_balance,
    get_epoch_start_slot,
    get_randao_mix,
    slot_to_epoch,
)
from eth2.beacon._utils.hash import (
    hash_eth2,
)
from eth2.beacon.types.attestations import Attestation
from eth2.beacon.types.crosslink_records import CrosslinkRecord
from eth2.beacon.types.states import BeaconState
from eth2.beacon.typing import (
    Epoch,
    Shard,
)


#
# Justification
#

def _current_previous_epochs_justifiable(
        state: BeaconState,
        current_epoch: Epoch,
        previous_epoch: Epoch,
        config: BeaconConfig) -> Tuple[bool, bool]:
    """
    Determine if epoch boundary attesting balance is greater than 2/3 of current_total_balance
    for current and previous epochs.
    """

    current_epoch_active_validator_indices = get_active_validator_indices(
        state.validator_registry,
        current_epoch,
    )
    previous_epoch_active_validator_indices = get_active_validator_indices(
        state.validator_registry,
        previous_epoch,
    )
    current_total_balance = get_total_balance(
        state.validator_balances,
        current_epoch_active_validator_indices,
        config.MAX_DEPOSIT_AMOUNT,
    )
    previous_total_balance = get_total_balance(
        state.validator_balances,
        previous_epoch_active_validator_indices,
        config.MAX_DEPOSIT_AMOUNT,
    )

    (
        previous_epoch_boundary_attesting_balance,
        current_epoch_boundary_attesting_balance
    ) = get_epoch_boundary_attesting_balances(current_epoch, previous_epoch, state, config)

    previous_epoch_justifiable = (
        3 * previous_epoch_boundary_attesting_balance >= 2 * previous_total_balance
    )
    current_epoch_justifiable = (
        3 * current_epoch_boundary_attesting_balance >= 2 * current_total_balance
    )
    return current_epoch_justifiable, previous_epoch_justifiable


def _get_finalized_epoch(
        justification_bitfield: int,
        previous_justified_epoch: Epoch,
        justified_epoch: Epoch,
        finalized_epoch: Epoch,
        previous_epoch: Epoch) -> Tuple[Epoch, int]:

    rule_1 = (
        (justification_bitfield >> 1) % 8 == 0b111 and
        previous_justified_epoch == previous_epoch - 2
    )
    rule_2 = (
        (justification_bitfield >> 1) % 4 == 0b11 and
        previous_justified_epoch == previous_epoch - 1
    )
    rule_3 = (
        justification_bitfield % 8 == 0b111 and
        justified_epoch == previous_epoch - 1
    )
    rule_4 = (
        justification_bitfield % 4 == 0b11 and
        justified_epoch == previous_epoch
    )
    # Check the rule in the order that can finalize higher epoch possible
    # The second output indicating what rule triggered is for testing purpose
    if rule_4:
        return justified_epoch, 4
    elif rule_3:
        return justified_epoch, 3
    elif rule_2:
        return previous_justified_epoch, 2
    elif rule_1:
        return previous_justified_epoch, 1
    else:
        return finalized_epoch, 0


def process_justification(state: BeaconState, config: BeaconConfig) -> BeaconState:

    current_epoch = state.current_epoch(config.EPOCH_LENGTH)
    previous_epoch = state.previous_epoch(config.EPOCH_LENGTH, config.GENESIS_EPOCH)

    current_epoch_justifiable, previous_epoch_justifiable = _current_previous_epochs_justifiable(
        state,
        current_epoch,
        previous_epoch,
        config,
    )

    _justification_bitfield = state.justification_bitfield << 1
    if previous_epoch_justifiable and current_epoch_justifiable:
        justification_bitfield = _justification_bitfield | 3
    elif previous_epoch_justifiable:
        justification_bitfield = _justification_bitfield | 2
    elif current_epoch_justifiable:
        justification_bitfield = _justification_bitfield | 1
    else:
        justification_bitfield = _justification_bitfield

    if current_epoch_justifiable:
        new_justified_epoch = current_epoch
    elif previous_epoch_justifiable:
        new_justified_epoch = previous_epoch
    else:
        new_justified_epoch = state.justified_epoch

    finalized_epoch, _ = _get_finalized_epoch(
        justification_bitfield,
        state.previous_justified_epoch,
        state.justified_epoch,
        state.finalized_epoch,
        previous_epoch,
    )

    return state.copy(
        previous_justified_epoch=state.justified_epoch,
        justified_epoch=new_justified_epoch,
        justification_bitfield=justification_bitfield,
        finalized_epoch=finalized_epoch,
    )


#
# Crosslinks
#
@to_tuple
def _filter_attestations_by_shard(
        attestations: Sequence[Attestation],
        shard: Shard) -> Iterable[Attestation]:
    for attestation in attestations:
        if attestation.data.shard == shard:
            yield attestation


def process_crosslinks(state: BeaconState, config: BeaconConfig) -> BeaconState:
    """
    Implement 'per-epoch-processing.crosslinks' portion of Phase 0 spec:
    https://github.com/ethereum/eth2.0-specs/blob/master/specs/core/0_beacon-chain.md#crosslinks

    For each shard from the past two epochs, find the shard block
    root that has been attested to by the most stake.
    If enough(>= 2/3 total stake) attesting stake, update the crosslink record of that shard.
    Return resulting ``state``
    """
    latest_crosslinks = state.latest_crosslinks
    previous_epoch_attestations = get_previous_epoch_attestations(
        state,
        config.EPOCH_LENGTH,
        config.GENESIS_EPOCH,
    )
    current_epoch_attestations = get_current_epoch_attestations(state, config.EPOCH_LENGTH)
    prev_epoch_start_slot = get_epoch_start_slot(
        state.previous_epoch(config.EPOCH_LENGTH, config.GENESIS_EPOCH),
        config.EPOCH_LENGTH,
    )
    next_epoch_start_slot = get_epoch_start_slot(
        state.next_epoch(config.EPOCH_LENGTH),
        config.EPOCH_LENGTH,
    )
    for slot in range(prev_epoch_start_slot, next_epoch_start_slot):
        crosslink_committees_at_slot = get_crosslink_committees_at_slot(
            state,
            slot,
            CommitteeConfig(config),
        )
        for crosslink_committee, shard in crosslink_committees_at_slot:
            try:
                winning_root, total_attesting_balance = get_winning_root(
                    state=state,
                    shard=shard,
                    # Use `_filter_attestations_by_shard` to filter out attestations
                    # not attesting to this shard so we don't need to going over
                    # irrelevent attestations over and over again.
                    attestations=_filter_attestations_by_shard(
                        previous_epoch_attestations + current_epoch_attestations,
                        shard,
                    ),
                    max_deposit_amount=config.MAX_DEPOSIT_AMOUNT,
                    committee_config=CommitteeConfig(config),
                )
            except NoWinningRootError:
                # No winning shard block root found for this shard.
                pass
            else:
                total_balance = sum(
                    get_effective_balance(state.validator_balances, i, config.MAX_DEPOSIT_AMOUNT)
                    for i in crosslink_committee
                )
                if 3 * total_attesting_balance >= 2 * total_balance:
                    latest_crosslinks = update_tuple_item(
                        latest_crosslinks,
                        shard,
                        CrosslinkRecord(
                            epoch=state.current_epoch(config.EPOCH_LENGTH),
                            shard_block_root=winning_root,
                        ),
                    )
                else:
                    # Don't update the crosslink of this shard
                    pass
    state = state.copy(
        latest_crosslinks=latest_crosslinks,
    )
    return state


#
# Validator registry and shuffling seed data
#
def _check_if_update_validator_registry(state: BeaconState,
                                        config: BeaconConfig) -> Tuple[bool, int]:
    if state.finalized_epoch <= state.validator_registry_update_epoch:
        return False, 0

    num_shards_in_committees = get_current_epoch_committee_count(
        state,
        shard_count=config.SHARD_COUNT,
        epoch_length=config.EPOCH_LENGTH,
        target_committee_size=config.TARGET_COMMITTEE_SIZE,
    )

    # Get every shard in the current committees
    shards = set(
        (state.current_epoch_start_shard + i) % config.SHARD_COUNT
        for i in range(num_shards_in_committees)
    )
    for shard in shards:
        if state.latest_crosslinks[shard].epoch <= state.validator_registry_update_epoch:
            return False, 0

    return True, num_shards_in_committees


def update_validator_registry(state: BeaconState) -> BeaconState:
    # TODO
    return state


def process_validator_registry(state: BeaconState,
                               config: BeaconConfig) -> BeaconState:
    state = state.copy(
        previous_calculation_epoch=state.current_calculation_epoch,
        previous_epoch_start_shard=state.current_epoch_start_shard,
        previous_epoch_seed=state.current_epoch_seed,
    )

    need_to_update, num_shards_in_committees = _check_if_update_validator_registry(state, config)

    if need_to_update:
        state = update_validator_registry(state)

        # Update step-by-step since updated `state.current_calculation_epoch`
        # is used to calculate other value). Follow the spec tightly now.
        state = state.copy(
            current_calculation_epoch=state.next_epoch(config.EPOCH_LENGTH),
        )
        state = state.copy(
            current_epoch_start_shard=(
                state.current_epoch_start_shard + num_shards_in_committees
            ) % config.SHARD_COUNT,
        )

        # The `helpers.generate_seed` function is only present to provide an entry point
        # for mocking this out in tests.
        current_epoch_seed = helpers.generate_seed(
            state=state,
            epoch=state.current_calculation_epoch,
            epoch_length=config.EPOCH_LENGTH,
            min_seed_lookahead=config.MIN_SEED_LOOKAHEAD,
            activation_exit_delay=config.ACTIVATION_EXIT_DELAY,
            latest_active_index_roots_length=config.LATEST_ACTIVE_INDEX_ROOTS_LENGTH,
            latest_randao_mixes_length=config.LATEST_RANDAO_MIXES_LENGTH,
        )
        state = state.copy(
            current_epoch_seed=current_epoch_seed,
        )
    else:
        epochs_since_last_registry_change = (
            state.current_epoch(config.EPOCH_LENGTH) - state.validator_registry_update_epoch
        )
        if is_power_of_two(epochs_since_last_registry_change):
            # Update step-by-step since updated `state.current_calculation_epoch`
            # is used to calculate other value). Follow the spec tightly now.
            state = state.copy(
                current_calculation_epoch=state.next_epoch(config.EPOCH_LENGTH),
            )

            # The `helpers.generate_seed` function is only present to provide an entry point
            # for mocking this out in tests.
            current_epoch_seed = helpers.generate_seed(
                state=state,
                epoch=state.current_calculation_epoch,
                epoch_length=config.EPOCH_LENGTH,
                min_seed_lookahead=config.MIN_SEED_LOOKAHEAD,
                activation_exit_delay=config.ACTIVATION_EXIT_DELAY,
                latest_active_index_roots_length=config.LATEST_ACTIVE_INDEX_ROOTS_LENGTH,
                latest_randao_mixes_length=config.LATEST_RANDAO_MIXES_LENGTH,
            )
            state = state.copy(
                current_epoch_seed=current_epoch_seed,
            )
        else:
            pass

    return state


#
# Final updates
#
def _update_latest_active_index_roots(state: BeaconState,
                                      committee_config: CommitteeConfig) -> BeaconState:
    """
    Return the BeaconState with updated `latest_active_index_roots`.
    """
    next_epoch = state.next_epoch(committee_config.EPOCH_LENGTH)

    # TODO: chanege to hash_tree_root
    active_validator_indices = get_active_validator_indices(
        state.validator_registry,
        Epoch(next_epoch + committee_config.ACTIVATION_EXIT_DELAY),
    )
    index_root = hash_eth2(
        b''.join(
            [
                index.to_bytes(32, 'big')
                for index in active_validator_indices
            ]
        )
    )

    latest_active_index_roots = update_tuple_item(
        state.latest_active_index_roots,
        (
            (next_epoch + committee_config.ACTIVATION_EXIT_DELAY) %
            committee_config.LATEST_ACTIVE_INDEX_ROOTS_LENGTH
        ),
        index_root,
    )

    return state.copy(
        latest_active_index_roots=latest_active_index_roots,
    )


def process_final_updates(state: BeaconState,
                          config: BeaconConfig) -> BeaconState:
    current_epoch = state.current_epoch(config.EPOCH_LENGTH)
    next_epoch = state.next_epoch(config.EPOCH_LENGTH)

    state = _update_latest_active_index_roots(state, CommitteeConfig(config))

    state = state.copy(
        latest_slashed_balances=update_tuple_item(
            state.latest_slashed_balances,
            next_epoch % config.LATEST_SLASHED_EXIT_LENGTH,
            state.latest_slashed_balances[current_epoch % config.LATEST_SLASHED_EXIT_LENGTH],
        ),
        latest_randao_mixes=update_tuple_item(
            state.latest_randao_mixes,
            next_epoch % config.LATEST_SLASHED_EXIT_LENGTH,
            get_randao_mix(
                state=state,
                epoch=current_epoch,
                epoch_length=config.EPOCH_LENGTH,
                latest_randao_mixes_length=config.LATEST_RANDAO_MIXES_LENGTH,
            ),
        ),
    )

    latest_attestations = tuple(
        filter(
            lambda attestation: (
                slot_to_epoch(attestation.data.slot, config.EPOCH_LENGTH) >= current_epoch
            ),
            state.latest_attestations
        )
    )
    state = state.copy(
        latest_attestations=latest_attestations,
    )

    return state
