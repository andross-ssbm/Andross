from typing import Any, Callable, Tuple
import logging

from sqlalchemy.exc import IntegrityError, DataError, OperationalError

from Andross.database.models import User, EntryDate, CharacterList, Elo, WinLoss, \
    DRP, DGP, Leaderboard, CharactersEntry, create_session


logger = logging.getLogger(f'andross.{__name__}')


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
    test = session.add(model_to_add)
    session.commit()
    session.flush()
    return model_to_add
