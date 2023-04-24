from datetime import datetime
from decimal import Decimal
import logging

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, DataError, OperationalError

from Andross.database.models import User, EntryDate, Elo, WinLoss, DRP, DGP, \
    CharactersEntry, Leaderboard, create_session, generate_latest_entry
from Andross.database.database_crud import generic_create

from Andross.slippi.slippi_api import get_player_ranked_data
from Andross.slippi.slippi_user import SlippiUser, Characters
from Andross.slippi.slippi_characters import get_character_id, get_character_name

logger = logging.getLogger(f'andross.{__name__}')


def get_all_users_ranked_list(session) -> bool | list[[User, SlippiUser]]:
    return_value = []
    try:
        users = session.query(User).all()
        for user in users:
            slippi_user = get_player_ranked_data(user.cc)
            if slippi_user:
                return_value.append([user, slippi_user])

        return return_value
    except OperationalError as e:
        logger.exception(f'Exception connecting to database: {e}')
        return False


def update_leaderboard() -> bool:
    ranked_data = []
    with create_session() as session:
        current_time = datetime.utcnow().replace(microsecond=0)
        results = generic_create(model=EntryDate, session=session, entry_time=current_time)
        date_entry = results[1]
        if not results[0]:
            logger.error(f'Unable to create date_entry: {current_time}')
            return False

        ranked_data = get_all_users_ranked_list(session)

        if not ranked_data:
            logger.warning(f'Unable to get users or slippi data')

        logger.info('Sorting users')
        sorted_ranked_data = sorted([(user.id, slippi_user) for user, slippi_user in ranked_data],
                                    key=lambda x: x[1].ranked_profile.rating_ordinal, reverse=True)

        counter = 1
        for user in sorted_ranked_data:
            try:
                local_id = user[0]
                slippi_data = user[1]

                if slippi_data.ranked_profile.wins or slippi_data.ranked_profile.losses:
                    test = Leaderboard(user_id=local_id,
                                       position=counter,
                                       elo=slippi_data.ranked_profile.rating_ordinal,
                                       wins=slippi_data.ranked_profile.wins,
                                       losses=slippi_data.ranked_profile.losses,
                                       drp=slippi_data.ranked_profile.daily_regional_placement,
                                       entry_time=current_time)
                    session.add(test)
                    session.commit()

                    counter += 1

            except (IntegrityError, DataError) as e:
                logger.exception(f'Exception running operation: {e}')
                session.rollback()
                return False
            except OperationalError as e:
                logger.exception(f'Exception connecting to database: {e}')
                return False
            except Exception as e:
                logger.exception(f'Unknown exception: {e}')
                session.rollback()
                raise e


def update_slippi_id(session, user: User, slippi_user: SlippiUser) -> bool:
    if user.slippi_id != slippi_user.ranked_profile.id:

        try:
            user.slippi_id = slippi_user.ranked_profile.id
            session.commit()
            return True
        except (IntegrityError, DataError) as e:
            logger.exception(f'Exception running operation: {e}')
            session.rollback()
            return False
        except OperationalError as e:
            logger.exception(f'Exception connecting to database: {e}')
            return False
        except Exception as e:
            logger.exception(f'Unknown exception: {e}')
            raise e
    return True


def update_elo(session, user: User, slippi_user: SlippiUser, entry_time: EntryDate) -> bool:
    if abs(user.latest_elo - slippi_user.ranked_profile.rating_ordinal) > 0.0001:
        elo_entry = Elo(user_id=user.id,
                        elo=slippi_user.ranked_profile.rating_ordinal,
                        entry_time=entry_time.entry_time)

        try:
            user.latest_elo = elo_entry.elo
            session.commit()
            session.add(elo_entry)
            session.commit()
            return True
        except (IntegrityError, DataError) as e:
            logger.exception(f'Exception running operation: {e}')
            session.rollback()
            return False
        except OperationalError as e:
            logger.exception(f'Exception connecting to database: {e}')
            return False
        except Exception as e:
            logger.exception(f'Unknown exception: {e}')
            raise e
    return True


def update_win_loss(session, user: User, slippi_user: SlippiUser, entry_time: EntryDate) -> bool:
    if user.latest_wins != slippi_user.ranked_profile.wins or user.latest_losses != slippi_user.ranked_profile.losses:
        win_loss_entry = WinLoss(user_id=user.id,
                                 wins=slippi_user.ranked_profile.wins,
                                 losses=slippi_user.ranked_profile.losses,
                                 entry_time=entry_time.entry_time)

        try:
            user.latest_wins = win_loss_entry.wins
            session.commit()
            user.latest_losses = win_loss_entry.losses
            session.commit()
            session.add(win_loss_entry)
            session.commit()
            return True
        except (IntegrityError, DataError) as e:
            logger.exception(f'Exception running operation: {e}')
            session.rollback()
            return False
        except OperationalError as e:
            logger.exception(f'Exception connecting to database: {e}')
            return False
        except Exception as e:
            logger.exception(f'Unknown exception: {e}')
            raise e
    return True


def update_drp(session, user: User, slippi_user: SlippiUser, entry_time: EntryDate) -> bool:
    if user.latest_drp != slippi_user.ranked_profile.daily_regional_placement:
        drp_entry = DRP(user_id=user.id,
                        placement=slippi_user.ranked_profile.daily_regional_placement,
                        entry_time=entry_time.entry_time)

        try:
            user.latest_drp = drp_entry.placement
            session.commit()
            session.add(drp_entry)
            session.commit()
            return True
        except (IntegrityError, DataError) as e:
            logger.exception(f'Exception running operation: {e}')
            session.rollback()
            return False
        except OperationalError as e:
            logger.exception(f'Exception connecting to database: {e}')
            return False
        except Exception as e:
            logger.exception(f'Unknown exception: {e}')
            raise e
    return True


def update_dgp(session, user: User, slippi_user: SlippiUser, entry_time: EntryDate) -> bool:
    try:
        latest_dgp_entry = generate_latest_entry(DGP)
        latest_dgp = (
            session.query(DGP)
            .join(latest_dgp_entry, latest_dgp_entry.c.user_id == DGP.user_id)
            .where(and_(DGP.user_id == user.id, DGP.entry_time == latest_dgp_entry.c.max_entry_time))
        )
        most_recent_entry = latest_dgp.first()

        if not most_recent_entry and not slippi_user.ranked_profile.daily_global_placement:
            return True

        dgp_entry = DGP(user_id=user.id,
                        placement=slippi_user.ranked_profile.daily_global_placement,
                        entry_time=entry_time.entry_time)

        if dgp_entry.placement == slippi_user.ranked_profile.daily_global_placement:
            return True

        session.add(dgp_entry)
        session.commit()
        return True

    except (IntegrityError, DataError) as e:
        logger.exception(f'Exception running operation: {e}')
        session.rollback()
        return False
    except OperationalError as e:
        logger.exception(f'Exception connecting to database: {e}')
        return False
    except Exception as e:
        logger.exception(f'Unknown exception: {e}')
        raise e


def update_character_entry(session, user: User, slippi_user: SlippiUser, entry_time: EntryDate) -> bool:
    try:

        if not len(slippi_user.ranked_profile.characters):
            return True

        latest_character_entry_entry = generate_latest_entry(CharactersEntry)
        latest_characters = (
            session.query(CharactersEntry)
            .join(latest_character_entry_entry, latest_character_entry_entry.c.user_id == CharactersEntry.user_id)
            .where(and_(CharactersEntry.user_id == user.id,
                        CharactersEntry.entry_time == latest_character_entry_entry.c.max_entry_time))

        )

        characters = latest_characters.all()
        local_characters_list = []
        for character in characters:
            local_characters_list.append(Characters(0,
                                                    get_character_name(character.character_id),
                                                    character.game_count))

        # Convert lists to dicts and check if they are different
        slippi_characters_dict = {c.character: c.game_count for c in slippi_user.ranked_profile.characters}
        local_characters_dict = {c.character: c.game_count for c in local_characters_list}
        if slippi_characters_dict == local_characters_dict:
            logger.debug(f'Character lists match')
            return True

        for character in slippi_user.ranked_profile.characters:
            session.add(CharactersEntry(character_id=get_character_id(character.character, dk_claus=True),
                                        user_id=user.id,
                                        game_count=character.game_count,
                                        entry_time=entry_time.entry_time))
            session.commit()
        main_id = get_character_id(max(slippi_user.ranked_profile.characters, key=lambda c: c.game_count).character,
                                   dk_claus=True)
        user.main_id = main_id
        session.commit()
        return True
    except (IntegrityError, DataError) as e:
        logger.exception(f'Exception running operation: {e}')
        session.rollback()
        return False
    except OperationalError as e:
        logger.exception(f'Exception connecting to database: {e}')
        return False
    except Exception as e:
        logger.exception(f'Unknown exception: {e}')
        raise e


def update_database(user: int = None) -> bool:
    logger.info('update_database')
    ranked_data = []
    with create_session() as session:

        # Get current time, create a EntryDate
        current_time = datetime.utcnow().replace(microsecond=0)
        results = generic_create(model=EntryDate, session=session, entry_time=current_time)
        date_entry = results[1]
        if not results[0]:
            logger.error(f'Unable to create date_entry: {current_time}')
            return False

        if not user:
            ranked_data = get_all_users_ranked_list(session)
        else:
            user = session.query(User).filter(User.id == user).first()
            ranked_data = [[user, get_player_ranked_data(user.cc)]]

        if not ranked_data:
            logger.warning(f'Unable to get users or slippi data')
            return False

        for data in ranked_data:
            local_data = data[0]
            slippi_data = data[1]

            if not slippi_data.ranked_profile.id:
                continue

            if not update_slippi_id(session, local_data, slippi_data):
                logger.warning(f'Unable to update users slippi_id: {local_data}')

            if not update_elo(session, local_data, slippi_data, date_entry):
                logger.warning(f'Unable to update elo: {local_data}')

            if not update_win_loss(session, local_data, slippi_data, date_entry):
                logger.warning(f'Unable to update win_losses: {local_data}')

            if not update_drp(session, local_data, slippi_data, date_entry):
                logger.warning(f'Unable to update daily_regional_placements: {local_data}')

            if not update_dgp(session, local_data, slippi_data, date_entry):
                logger.warning(f'Unable to update daily_global_placements: {local_data}')

            if not update_character_entry(session, local_data, slippi_data, date_entry):
                logger.warning(f'Unable to update character_entry: {local_data}')

        session.commit()
        logger.info('Updated database')
        return True
