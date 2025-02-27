import pytest

from eth._utils.address import (
    force_bytes_to_address,
)
from eth.estimators.gas import (
    binary_gas_search_1000_tolerance,
)
from eth.vm.forks import (
    ArrowGlacierVM,
    BerlinVM,
    ByzantiumVM,
    ConstantinopleVM,
    FrontierVM,
    HomesteadVM,
    IstanbulVM,
    LondonVM,
    MuirGlacierVM,
    PetersburgVM,
    SpuriousDragonVM,
    TangerineWhistleVM,
)
from tests.core.helpers import (
    fill_block,
)
from tests.tools.factories.transaction import (
    new_transaction,
)

ADDRESS_2 = b"\0" * 19 + b"\x02"

ADDR_1010 = force_bytes_to_address(b"\x10\x10")


@pytest.mark.parametrize(
    "should_sign_tx",
    (True, False),
)
@pytest.mark.parametrize(
    "data, gas_estimator, to, on_pending, vm_cls, expected",
    (
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            FrontierVM,
            21000,
            id="simple default pending for FrontierVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            FrontierVM,
            21000,
            id="simple default for FrontierVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            FrontierVM,
            21680,
            id="10 bytes default pending for FrontierVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            FrontierVM,
            21680,
            id="10 bytes default for FrontierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            FrontierVM,
            35333,
            id="sha3 precompile 32 bytes default pending for FrontierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            FrontierVM,
            35345,
            id="sha3 precompile 32 bytes default for FrontierVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            FrontierVM,
            54840,
            id="sha3 precompile 320 bytes default pending for FrontierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            FrontierVM,
            23935,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for FrontierVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            HomesteadVM,
            21000,
            id="simple default pending for HomesteadVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            HomesteadVM,
            21000,
            id="simple default for HomesteadVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            HomesteadVM,
            21680,
            id="10 bytes default pending for HomesteadVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            HomesteadVM,
            21680,
            id="10 bytes default for HomesteadVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            HomesteadVM,
            35333,
            id="sha3 precompile 32 bytes default pending for HomesteadVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            HomesteadVM,
            35345,
            id="sha3 precompile 32 bytes default for HomesteadVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            HomesteadVM,
            54840,
            id="sha3 precompile 320 bytes default pending for HomesteadVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            HomesteadVM,
            23935,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for HomesteadVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            TangerineWhistleVM,
            21000,
            id="simple default pending for TangerineWhistleVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            TangerineWhistleVM,
            21000,
            id="simple default for TangerineWhistleVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            TangerineWhistleVM,
            21680,
            id="10 bytes default pending for TangerineWhistleVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            TangerineWhistleVM,
            21680,
            id="10 bytes default for TangerineWhistleVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            TangerineWhistleVM,
            35333,
            id="sha3 precompile 32 bytes default pending for TangerineWhistleVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            TangerineWhistleVM,
            35345,
            id="sha3 precompile 32 bytes default for TangerineWhistleVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            TangerineWhistleVM,
            54840,
            id="sha3 precompile 320 bytes default pending for TangerineWhistleVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            TangerineWhistleVM,
            23935,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for TangerineWhistleVM",  # noqa: E501
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            SpuriousDragonVM,
            21000,
            id="simple default pending for SpuriousDragonVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            SpuriousDragonVM,
            21000,
            id="simple default for SpuriousDragonVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            SpuriousDragonVM,
            21680,
            id="10 bytes default pending for SpuriousDragonVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            SpuriousDragonVM,
            21680,
            id="10 bytes default for SpuriousDragonVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            SpuriousDragonVM,
            35333,
            id="sha3 precompile 32 bytes default pending for SpuriousDragonVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            SpuriousDragonVM,
            35345,
            id="sha3 precompile 32 bytes default for SpuriousDragonVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            SpuriousDragonVM,
            54840,
            id="sha3 precompile 320 bytes default pending for SpuriousDragonVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            SpuriousDragonVM,
            23935,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for SpuriousDragonVM",  # noqa: E501
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            ByzantiumVM,
            21000,
            id="simple default pending for ByzantiumVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            ByzantiumVM,
            21000,
            id="simple default for ByzantiumVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            ByzantiumVM,
            21680,
            id="10 bytes default pending for ByzantiumVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            ByzantiumVM,
            21680,
            id="10 bytes default for ByzantiumVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            ByzantiumVM,
            35333,
            id="sha3 precompile 32 bytes default pending for ByzantiumVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            ByzantiumVM,
            35345,
            id="sha3 precompile 32 bytes default for ByzantiumVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            ByzantiumVM,
            54840,
            id="sha3 precompile 320 bytes default pending for ByzantiumVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            ByzantiumVM,
            23935,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for ByzantiumVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            ConstantinopleVM,
            21000,
            id="simple default pending for ConstantinopleVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            ConstantinopleVM,
            21000,
            id="simple default for ConstantinopleVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            ConstantinopleVM,
            21680,
            id="10 bytes default pending for ConstantinopleVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            ConstantinopleVM,
            21680,
            id="10 bytes default for ConstantinopleVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            ConstantinopleVM,
            35333,
            id="sha3 precompile 32 bytes default pending for ConstantinopleVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            ConstantinopleVM,
            35345,
            id="sha3 precompile 32 bytes default for ConstantinopleVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            ConstantinopleVM,
            54840,
            id="sha3 precompile 320 bytes default pending for ConstantinopleVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            ConstantinopleVM,
            23935,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for ConstantinopleVM",  # noqa: E501
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            PetersburgVM,
            21000,
            id="simple default pending for PetersburgVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            PetersburgVM,
            21000,
            id="simple default for PetersburgVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            PetersburgVM,
            21680,
            id="10 bytes default pending for PetersburgVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            PetersburgVM,
            21680,
            id="10 bytes default for PetersburgVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            PetersburgVM,
            35333,
            id="sha3 precompile 32 bytes default pending for PetersburgVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            PetersburgVM,
            35345,
            id="sha3 precompile 32 bytes default for PetersburgVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            PetersburgVM,
            54840,
            id="sha3 precompile 320 bytes default pending for PetersburgVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            PetersburgVM,
            23935,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for PetersburgVM",  # noqa: E501
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            IstanbulVM,
            21000,
            id="simple default pending for IstanbulVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            IstanbulVM,
            21000,
            id="simple default for IstanbulVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            IstanbulVM,
            21160,
            id="10 bytes default pending for IstanbulVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            IstanbulVM,
            21160,
            id="10 bytes default for IstanbulVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            IstanbulVM,
            33675,
            id="sha3 precompile 32 bytes default pending for IstanbulVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            IstanbulVM,
            33687,
            id="sha3 precompile 32 bytes default for IstanbulVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            IstanbulVM,
            38265,
            id="sha3 precompile 320 bytes default pending for IstanbulVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            IstanbulVM,
            22272,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for IstanbulVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            MuirGlacierVM,
            21000,
            id="simple default pending for MuirGlacierVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            MuirGlacierVM,
            21000,
            id="simple default for MuirGlacierVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            MuirGlacierVM,
            21160,
            id="10 bytes default pending for MuirGlacierVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            MuirGlacierVM,
            21160,
            id="10 bytes default for MuirGlacierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            MuirGlacierVM,
            33675,
            id="sha3 precompile 32 bytes default pending for MuirGlacierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            MuirGlacierVM,
            33687,
            id="sha3 precompile 32 bytes default for MuirGlacierVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            MuirGlacierVM,
            38265,
            id="sha3 precompile 320 bytes default pending for MuirGlacierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            MuirGlacierVM,
            22272,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for MuirGlacierVM",  # noqa: E501
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            BerlinVM,
            21000,
            id="simple default pending for BerlinVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            BerlinVM,
            21000,
            id="simple default for BerlinVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            BerlinVM,
            21160,
            id="10 bytes default pending for BerlinVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            BerlinVM,
            21160,
            id="10 bytes default for BerlinVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            BerlinVM,
            33675,
            id="sha3 precompile 32 bytes default pending for BerlinVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            BerlinVM,
            33687,
            id="sha3 precompile 32 bytes default for BerlinVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            BerlinVM,
            38265,
            id="sha3 precompile 320 bytes default pending for BerlinVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            BerlinVM,
            22272,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for BerlinVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            LondonVM,
            21000,
            id="simple default pending for LondonVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            LondonVM,
            21000,
            id="simple default for LondonVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            LondonVM,
            21160,
            id="10 bytes default pending for LondonVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            LondonVM,
            21160,
            id="10 bytes default for LondonVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            LondonVM,
            33675,
            id="sha3 precompile 32 bytes default pending for LondonVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            LondonVM,
            33687,
            id="sha3 precompile 32 bytes default for LondonVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            LondonVM,
            38265,
            id="sha3 precompile 320 bytes default pending for LondonVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            LondonVM,
            22272,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for LondonVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            True,
            ArrowGlacierVM,
            21000,
            id="simple default pending for ArrowGlacierVM",
        ),
        pytest.param(
            b"",
            None,
            ADDR_1010,
            False,
            ArrowGlacierVM,
            21000,
            id="simple default for ArrowGlacierVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            True,
            ArrowGlacierVM,
            21160,
            id="10 bytes default pending for ArrowGlacierVM",
        ),
        pytest.param(
            b"\xff" * 10,
            None,
            ADDR_1010,
            False,
            ArrowGlacierVM,
            21160,
            id="10 bytes default for ArrowGlacierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            True,
            ArrowGlacierVM,
            33675,
            id="sha3 precompile 32 bytes default pending for ArrowGlacierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            None,
            ADDRESS_2,
            False,
            ArrowGlacierVM,
            33687,
            id="sha3 precompile 32 bytes default for ArrowGlacierVM",
        ),
        pytest.param(
            b"\xff" * 320,
            None,
            ADDRESS_2,
            True,
            ArrowGlacierVM,
            38265,
            id="sha3 precompile 320 bytes default pending for ArrowGlacierVM",
        ),
        pytest.param(
            b"\xff" * 32,
            binary_gas_search_1000_tolerance,
            ADDRESS_2,
            True,
            ArrowGlacierVM,
            22272,
            id="sha3 precompile 32 bytes 1000_tolerance binary pending for ArrowGlacierVM",  # noqa: E501
        ),
    ),
)
def test_estimate_gas(
    chain_without_block_validation_from_vm,
    data,
    gas_estimator,
    to,
    on_pending,
    vm_cls,
    expected,
    funded_address,
    funded_address_private_key,
    should_sign_tx,
):
    chain = chain_without_block_validation_from_vm(vm_cls)
    if gas_estimator:
        chain.gas_estimator = gas_estimator
    vm = chain.get_vm()
    amount = 100
    from_ = funded_address

    tx_params = dict(vm=vm, from_=from_, to=to, amount=amount, data=data)

    # either make a signed or unsigned transaction
    if should_sign_tx:
        tx = new_transaction(private_key=funded_address_private_key, **tx_params)
    else:
        tx = new_transaction(**tx_params)

    if on_pending:
        # estimate on *pending* block
        pending_header = chain.create_header_from_parent(chain.get_canonical_head())
        assert chain.estimate_gas(tx, pending_header) == expected
    else:
        # estimates on top of *latest* block
        assert chain.estimate_gas(tx) == expected
        # these are long, so now that we know the exact numbers let's skip the repeat
        # test assert chain.estimate_gas(tx, chain.get_canonical_head()) == expected


@pytest.mark.parametrize(
    "vm_cls, expected",
    (
        (FrontierVM, 722760),
        (
            HomesteadVM.configure(
                support_dao_fork=False,
            ),
            722760,
        ),
        (TangerineWhistleVM, 722760),
        (SpuriousDragonVM, 722760),
        (ByzantiumVM, 722760),
        (ConstantinopleVM, 722760),
        (PetersburgVM, 722760),
        (IstanbulVM, 186120),
        (MuirGlacierVM, 186120),
        (BerlinVM, 186120),
        (LondonVM, 186120),
    ),
)
def test_estimate_gas_on_full_block(
    chain_without_block_validation_from_vm,
    vm_cls,
    expected,
    funded_address_private_key,
    funded_address,
):
    def mk_estimation_txn(chain, from_, from_key, data):
        vm = chain.get_vm()
        tx_params = dict(
            from_=from_,
            to=ADDR_1010,
            amount=200,
            private_key=from_key,
            gas=chain.header.gas_limit,
            data=data,
        )
        return new_transaction(vm, **tx_params)

    chain = chain_without_block_validation_from_vm(vm_cls)
    from_ = funded_address
    from_key = funded_address_private_key
    garbage_data = (
        b"""
        fill up the block much faster because this transaction contains a bunch of extra
        garbage_data, which doesn't add to execution time, just the gas costs
    """
        * 30
    )
    gas = 375000

    # fill the canonical head
    fill_block(chain, from_, from_key, gas, garbage_data)
    chain.import_block(chain.get_vm().get_block())

    # build a transaction to estimate gas for
    next_canonical_tx = mk_estimation_txn(chain, from_, from_key, data=garbage_data * 2)

    assert chain.estimate_gas(next_canonical_tx) == expected

    # fill the pending block
    fill_block(chain, from_, from_key, gas, garbage_data)

    # build a transaction to estimate gas for
    next_pending_tx = mk_estimation_txn(chain, from_, from_key, data=garbage_data * 2)

    assert chain.estimate_gas(next_pending_tx, chain.header) == expected
