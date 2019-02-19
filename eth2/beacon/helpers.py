from typing import (
    Sequence,
    Tuple,
    TYPE_CHECKING,
)


from eth_utils import (
    ValidationError,
)
from eth_typing import (
    Hash32,
)

from eth2.beacon._utils.hash import (
    hash_eth2,
)
from eth2.beacon.enums import (
    SignatureDomain,
)
from eth2.beacon.typing import (
    Epoch,
    Gwei,
    Slot,
    ValidatorIndex,
)
from eth2.beacon.validation import (
    validate_epoch_for_active_index_root,
    validate_epoch_for_active_randao_mix,
)

if TYPE_CHECKING:
    from eth2.beacon.types.attestation_data import AttestationData  # noqa: F401
    from eth2.beacon.types.states import BeaconState  # noqa: F401
    from eth2.beacon.types.forks import Fork  # noqa: F401
    from eth2.beacon.types.slashable_attestations import SlashableAttestation  # noqa: F401
    from eth2.beacon.types.validator_records import ValidatorRecord  # noqa: F401


#
# Time unit convertion
#
def slot_to_epoch(slot: Slot, epoch_length: int) -> Epoch:
    return Epoch(slot // epoch_length)


def get_epoch_start_slot(epoch: Epoch, epoch_length: int) -> Slot:
    return Slot(epoch * epoch_length)


def _get_block_root(
        latest_block_roots: Sequence[Hash32],
        state_slot: Slot,
        slot: Slot,
        latest_block_roots_length: int) -> Hash32:
    """
    Return the block root at a recent ``slot``.
    """
    if state_slot > slot + latest_block_roots_length:
        raise ValidationError(
            "state.slot ({}) should be less than or equal to "
            "(slot + latest_block_roots_length) ({}), "
            "where slot={}, latest_block_roots_length={}".format(
                state_slot,
                slot + latest_block_roots_length,
                slot,
                latest_block_roots_length,
            )
        )
    if slot >= state_slot:
        raise ValidationError(
            "slot ({}) should be less than state.slot ({})".format(
                slot,
                state_slot,
            )
        )
    return latest_block_roots[slot % latest_block_roots_length]


def get_block_root(
        state: 'BeaconState',
        slot: Slot,
        latest_block_roots_length: int) -> Hash32:
    """
    Return the block root at a recent ``slot``.
    """
    return _get_block_root(
        state.latest_block_roots,
        state.slot,
        slot,
        latest_block_roots_length,
    )


def get_randao_mix(state: 'BeaconState',
                   epoch: Epoch,
                   epoch_length: int,
                   latest_randao_mixes_length: int) -> Hash32:
    """
    Return the randao mix at a recent ``epoch``.
    """
    validate_epoch_for_active_randao_mix(
        state.current_epoch(epoch_length),
        epoch,
        latest_randao_mixes_length,
    )

    return state.latest_randao_mixes[epoch % latest_randao_mixes_length]


def get_active_validator_indices(validators: Sequence['ValidatorRecord'],
                                 epoch: Epoch) -> Tuple[ValidatorIndex, ...]:
    """
    Get indices of active validators from ``validators``.
    """
    return tuple(
        ValidatorIndex(index)
        for index, validator in enumerate(validators)
        if validator.is_active(epoch)
    )


def generate_seed(state: 'BeaconState',
                  epoch: Epoch,
                  epoch_length: int,
                  min_seed_lookahead: int,
                  activation_exit_delay: int,
                  latest_active_index_roots_length: int,
                  latest_randao_mixes_length: int) -> Hash32:
    """
    Generate a seed for the given ``epoch``.
    """
    randao_mix = get_randao_mix(
        state=state,
        epoch=Epoch(epoch - min_seed_lookahead),
        epoch_length=epoch_length,
        latest_randao_mixes_length=latest_randao_mixes_length,
    )
    active_index_root = get_active_index_root(
        state=state,
        epoch=epoch,
        epoch_length=epoch_length,
        activation_exit_delay=activation_exit_delay,
        latest_active_index_roots_length=latest_active_index_roots_length,
    )
    epoch_as_bytes = epoch.to_bytes(32, byteorder="little")

    return hash_eth2(randao_mix + active_index_root + epoch_as_bytes)


def get_active_index_root(state: 'BeaconState',
                          epoch: Epoch,
                          epoch_length: int,
                          activation_exit_delay: int,
                          latest_active_index_roots_length: int) -> Hash32:
    """
    Return the index root at a recent ``epoch``.
    """
    validate_epoch_for_active_index_root(
        state.current_epoch(epoch_length),
        epoch,
        activation_exit_delay,
        latest_active_index_roots_length,
    )

    return state.latest_active_index_roots[epoch % latest_active_index_roots_length]


def get_effective_balance(
        validator_balances: Sequence[Gwei],
        index: ValidatorIndex,
        max_deposit_amount: Gwei) -> Gwei:
    """
    Return the effective balance (also known as "balance at stake") for a
    ``validator`` with the given ``index``.
    """
    return min(validator_balances[index], max_deposit_amount)


def get_total_balance(validator_balances: Sequence[Gwei],
                      validator_indices: Sequence[ValidatorIndex],
                      max_deposit_amount: Gwei) -> Gwei:
    """
    Return the combined effective balance of an array of validators.
    """
    return Gwei(sum(
        get_effective_balance(validator_balances, index, max_deposit_amount)
        for index in validator_indices
    ))


def get_fork_version(fork: 'Fork',
                     epoch: Epoch) -> int:
    """
    Return the current ``fork_version`` from the given ``fork`` and ``epoch``.
    """
    if epoch < fork.epoch:
        return fork.previous_version
    else:
        return fork.current_version


def get_domain(fork: 'Fork',
               epoch: Epoch,
               domain_type: SignatureDomain) -> int:
    """
    Return the domain number of the current fork and ``domain_type``.
    """
    # 2 ** 32 = 4294967296
    return get_fork_version(
        fork,
        epoch,
    ) * 4294967296 + domain_type


def is_double_vote(attestation_data_1: 'AttestationData',
                   attestation_data_2: 'AttestationData',
                   epoch_length: int) -> bool:
    """
    Assumes ``attestation_data_1`` is distinct from ``attestation_data_2``.

    Return True if the provided ``AttestationData`` are slashable
    due to a 'double vote'.
    """
    return (
        slot_to_epoch(attestation_data_1.slot, epoch_length) ==
        slot_to_epoch(attestation_data_2.slot, epoch_length)
    )


def is_surround_vote(attestation_data_1: 'AttestationData',
                     attestation_data_2: 'AttestationData',
                     epoch_length: int) -> bool:
    """
    Assumes ``attestation_data_1`` is distinct from ``attestation_data_2``.

    Return True if the provided ``AttestationData`` are slashable
    due to a 'surround vote'.

    Note: parameter order matters as this function only checks
    that ``attestation_data_1`` surrounds ``attestation_data_2``.
    """
    source_epoch_1 = attestation_data_1.justified_epoch
    source_epoch_2 = attestation_data_2.justified_epoch
    target_epoch_1 = slot_to_epoch(attestation_data_1.slot, epoch_length)
    target_epoch_2 = slot_to_epoch(attestation_data_2.slot, epoch_length)
    return source_epoch_1 < source_epoch_2 and target_epoch_2 < target_epoch_1


def get_entry_exit_effect_epoch(
        epoch: Epoch,
        activation_exit_delay: int) -> Epoch:
    """
    An entry or exit triggered in the ``epoch`` given by the input takes effect at
    the epoch given by the output.
    """
    return Epoch(epoch + 1 + activation_exit_delay)
