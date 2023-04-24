from dataclasses import dataclass
from decimal import Decimal

import logging

logger = logging.getLogger(f'andross.{__name__}')


@dataclass
class Rank:
    lower_bound: Decimal
    upper_bound: Decimal
    rank_name: str


class GrandMaster(Rank):
    rank_name = 'Grandmaster'


grand_master = GrandMaster(lower_bound='2191.75', upper_bound=Decimal('infinity'), rank_name='Grandmaster')
rank_list = [
    Rank(Decimal('0'), Decimal('765.42'), 'Bronze 1'),
    Rank(Decimal('765.43'), Decimal('913.71'), 'Bronze 2'),
    Rank(Decimal('913.72'), Decimal('1054.86'), 'Bronze 3'),
    Rank(Decimal('1054.87'), Decimal('1188.87'), 'Silver 1'),
    Rank(Decimal('1188.88'), Decimal('1315.74'), 'Silver 2'),
    Rank(Decimal('1315.75'), Decimal('1435.47'), 'Silver 3'),
    Rank(Decimal('1435.48'), Decimal('1548.06'), 'Gold 1'),
    Rank(Decimal('1548.07'), Decimal('1653.51'), 'Gold 2'),
    Rank(Decimal('1653.52'), Decimal('1751.82'), 'Gold 3'),
    Rank(Decimal('1751.83'), Decimal('1842.99'), 'Platinum 1'),
    Rank(Decimal('1843'), Decimal('1927.02'), 'Platinum 2'),
    Rank(Decimal('1927.03'), Decimal('2003.91'), 'Platinum 3'),
    Rank(Decimal('2003.92'), Decimal('2073.66'), 'Diamond 1'),
    Rank(Decimal('2073.67'), Decimal('2136.27'), 'Diamond 2'),
    Rank(Decimal('2136.28'), Decimal('2191.74'), 'Diamond 3'),
    Rank(Decimal('2191.75'), Decimal('2274.99'), 'Master 1'),
    Rank(Decimal('2275'), Decimal('2350'), 'Master 2'),
    Rank(Decimal('2350'), Decimal('Infinity'), 'Master 3')
]


def get_rank(elo: Decimal, daily_regional_placement: int = None):
    if daily_regional_placement:
        return grand_master.rank_name

    for rank in rank_list:
        if rank.lower_bound <= elo < rank.upper_bound:
            return rank.rank_name

    # If score is greater than the upper bound of the last rank, return the highest rank
    return rank_list[-1].rank_name
