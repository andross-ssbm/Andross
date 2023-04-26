from typing import Any, Callable, Tuple
import logging

from sqlalchemy.exc import IntegrityError, DataError, OperationalError
from sqlalchemy import or_

from Andross.database.models import User, EntryDate, CharacterList, Elo, WinLoss, \
    DRP, DGP, Leaderboard, CharactersEntry, create_session


logger = logging.getLogger(f'andross.{__name__}')


def create_user(user_id: int, cc: str, name: str) -> bool:
    logger.info(f'create_user: {user_id}, {cc}, {name}')
    try:
        with create_session() as session:
            session.add(User(id=user_id, cc=cc, name=name))
            session.commit()
            return True
    except (IntegrityError, DataError) as e:
        logger.error(f'Error running operation: {e}')
        session.rollback()
        return False
    except OperationalError as e:
        logger.error(f'Error connecting to database: {e}')
        return False


def get_user(user_id: int, user_cc: str = None) -> Tuple[bool, User | None]:
    logger.info(f'get_user: {user_id}, {user_cc}')
    try:
        with create_session() as session:
            results = session.query(User).filter(or_(User.id == user_id, User.cc == user_cc)).first()
            if not results:
                logger.info('Unable to get user')
                return False, None
            return True, results
    except (IntegrityError, DataError) as e:
        logger.error(f'Error running operation: {e}')
        session.rollback()
        return False, None
    except OperationalError as e:
        logger.error(f'Error connecting to database: {e}')
        return False, None


def get_all_elo(user_id: int) -> tuple[bool, None] | tuple[bool, list[Elo]]:
    logger.info(f'get_all_elo: {user_id}')
    try:
        with create_session() as session:
            results = session.query(Elo).filter(Elo.user_id == user_id).order_by(Elo.entry_time.asc()).all()
            if not results:
                logger.info('Unable to get elo')
                return False, None
            return True, results
    except (IntegrityError, DataError) as e:
        logger.error(f'Error running operation: {e}')
        session.rollback()
        return False, None
    except OperationalError as e:
        logger.error(f'Error connecting to database: {e}')
        return False, None


def error_handler(func: Callable[..., Any]) -> Callable[..., Tuple[bool, Any]]:
    def wrapper(*args: Any, **kwargs: Any) -> Tuple[bool, Any]:
        try:
            results = func(*args, **kwargs)
            return True, results
        except (IntegrityError, DataError) as e:
            logger.error(f'Error running operation: {e}')
            session = kwargs.get('session')
            session.rollback()
            return False, None
        except OperationalError as e:
            logger.error(f'Error connecting to database: {e}')
            return False, None
        except Exception as e:
            raise

    return wrapper


@error_handler
def generic_create(**kwargs):
    # Get session from kwargs and put into local variable then pop, so we can pass the kwargs to the model
    session = kwargs.get('session')
    kwargs.pop('session', None)

    # Get model from kwargs and put into local variable then pop, so we can pass kwargs to model
    model = kwargs.get('model')
    kwargs.pop('model', None)

    model_to_add = model(**kwargs)
    session.add(model_to_add)
    session.commit()
    session.flush()
    return model_to_add
