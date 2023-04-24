from decimal import Decimal

from Andross.slippi.slippi_ranks import get_rank


def test_get_rank():
    assert get_rank(0) == 'Bronze 1'
    assert get_rank(Decimal('800')) == 'Bronze 2'
    assert get_rank(Decimal('1000')) == 'Bronze 3'
    assert get_rank(Decimal('1100')) == 'Silver 1'
    assert get_rank(Decimal('1300')) == 'Silver 2'
    assert get_rank(Decimal('1400')) == 'Silver 3'
    assert get_rank(Decimal('1500')) == 'Gold 1'
    assert get_rank(Decimal('1600')) == 'Gold 2'
    assert get_rank(Decimal('1700')) == 'Gold 3'
    assert get_rank(Decimal('1800')) == 'Platinum 1'
    assert get_rank(Decimal('1900')) == 'Platinum 2'
    assert get_rank(Decimal('2000')) == 'Platinum 3'
    assert get_rank(Decimal('2050')) == 'Diamond 1'
    assert get_rank(Decimal('2100')) == 'Diamond 2'
    assert get_rank(Decimal('2150')) == 'Diamond 3'
    assert get_rank(Decimal('2200')) == 'Master 1'
    assert get_rank(Decimal('2300')) == 'Master 2'
    assert get_rank(Decimal('2500')) == 'Master 3'
    assert get_rank(Decimal('2500'), 1) == 'Grandmaster'

