from sqlalchemy import select, func, and_
from datetime import datetime
from decimal import Decimal
from typing import Tuple, Any
import logging

from Andross.database.models import create_session, \
    User, CharacterList, EntryDate, Elo, WinLoss, DRP, DGP, Leaderboard, CharactersEntry, generate_latest_entry

logger = logging.getLogger(f'andross.{__name__}')


leaderboard_type = [str, str, Decimal, int, int, int, int]  # name, cc, elo, wins, losses, drp, user.id


def get_users_latest_placement(user: User) -> int:
    logger.info(f'get_users_latest_placement: {user}')

    with create_session() as session:
        latest_leaderboard_by_date_id = (
            session.query(Leaderboard)
            .filter(Leaderboard.user_id == user.id)
            .group_by(Leaderboard.user_id)
            .having(func.max(Leaderboard.entry_time))
            .order_by(func.max(Leaderboard.entry_time).desc()).first()
        )
        if not latest_leaderboard_by_date_id:
            return 0
        return latest_leaderboard_by_date_id.position


def get_writeable_leaderboard() -> Tuple[bool, list[list[Any]] | None]:
    logger.info('get_writeable_leaderboard')

    latest_elo = generate_latest_entry(Elo)

    latest_win_losses = generate_latest_entry(WinLoss)

    latest_drp = generate_latest_entry(DRP)

    with create_session() as session:
        # Build the query
        query = (
            session.query(User.id, Elo.elo, WinLoss.wins, WinLoss.losses, DRP.placement)
            .join(latest_elo, latest_elo.c.user_id == User.id)
            .join(Elo, and_(Elo.user_id == latest_elo.c.user_id, Elo.entry_time == latest_elo.c.max_entry_time))
            .outerjoin(latest_win_losses, latest_win_losses.c.user_id == User.id)
            .outerjoin(WinLoss, and_(WinLoss.user_id == latest_win_losses.c.user_id,
                                     WinLoss.entry_time == latest_win_losses.c.max_entry_time))
            .outerjoin(latest_drp, latest_drp.c.user_id == User.id)
            .outerjoin(DRP, and_(DRP.user_id == latest_drp.c.user_id, DRP.entry_time == latest_drp.c.max_entry_time))
            .order_by(Elo.elo.desc())
        )

        logger.debug(f'query: {query}')

        return_value = session.execute(query).all()
    if not return_value:
        return False, None

    return True, [list(row) for row in return_value]


def get_leaderboard_between(
        end_datetime: datetime,
        start_datetime: datetime = datetime(2021, 1, 1)) -> Tuple[bool, list[leaderboard_type] | None]:

    logger.info(f'get_leaderboard_between: {start_datetime} -> {end_datetime}')

    def _generate_latest_entry(model):
        return (
            select(model.user_id, func.max(model.entry_time).label('max_entry_time'))
            .where(model.entry_time.between(start_datetime, end_datetime))
            .group_by(model.user_id)
            .alias()
        )

    latest_elo = _generate_latest_entry(Elo)

    latest_win_losses = _generate_latest_entry(WinLoss)

    latest_drp = _generate_latest_entry(DRP)

    with create_session() as session:
        # Build the query
        query = (
            session.query(User.name, User.cc, Elo.elo, WinLoss.wins, WinLoss.losses, DRP.placement, User.id)
            .join(latest_elo, latest_elo.c.user_id == User.id)
            .join(Elo, and_(Elo.user_id == latest_elo.c.user_id, Elo.entry_time == latest_elo.c.max_entry_time))
            .outerjoin(latest_win_losses, latest_win_losses.c.user_id == User.id)
            .outerjoin(WinLoss, and_(WinLoss.user_id == latest_win_losses.c.user_id,
                                     WinLoss.entry_time == latest_win_losses.c.max_entry_time))
            .outerjoin(latest_drp, latest_drp.c.user_id == User.id)
            .outerjoin(DRP, and_(DRP.user_id == latest_drp.c.user_id, DRP.entry_time == latest_drp.c.max_entry_time))
            .order_by(Elo.elo.desc())
        )

        logger.debug(f'query: {query}')

        return_value = session.execute(query).all()
    if not return_value:
        return False, None

    return True, [row for row in return_value]


def get_leaderboard_quick() -> Tuple[bool, list[leaderboard_type] | None]:
    logger.info('get_leaderboard_quick')

    leaderboard_return = []
    with create_session() as session:
        leaderboard = (
            session.query(User)
            .filter(and_(User.latest_wins != 0, User.latest_losses != 0))
            .order_by(User.latest_elo.desc())
        )
        logger.debug(f'leaderboard query: {leaderboard}')

        leaderboard_return = leaderboard.all()

    if not leaderboard_return:
        return False, None

    return True, leaderboard_return


def get_leaderboard_standard() -> Tuple[bool, list[leaderboard_type] | None]:
    logger.info('get_leaderboard_standard')

    leaderboard_return = []
    with create_session() as session:
        leaderboard = session.query(
            User.name,
            User.cc,
            Elo.elo,
            User.latest_wins,
            User.latest_losses,
            User.latest_drp,
            User.id
            )\
            .join(Elo, User.id == Elo.user_id)\
            .filter(Elo.entry_time == session.query(func.max(Elo.entry_time))
                    .filter(Elo.user_id == User.id).scalar()).order_by(Elo.elo.desc()).all()

    if not leaderboard:
        return False, None

    return True, leaderboard



