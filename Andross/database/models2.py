import os
import random
from datetime import datetime
import logging

from sqlalchemy import create_engine, Integer, BigInteger, \
    String, Numeric, DateTime, Index, ForeignKey, func, and_, select
from sqlalchemy.orm import relationship, DeclarativeBase, sessionmaker, Mapped, mapped_column

from Andross.slippi.slippi_characters import SlippiCharacterId
from Andross.slippi.slippi_ranks import get_rank

# Database variables
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# create the database engine
engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}', echo=True)


def create_session():
    _session = sessionmaker(bind=engine)
    session = _session()
    return session


# create a declarative base for defining ORM classes
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cc: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(14), nullable=False)
    main_id: Mapped[int] = mapped_column(Integer, ForeignKey('character_list.id'), server_default='256', default=256)
    slippi_id: Mapped[int] = mapped_column(BigInteger, server_default='0', default=0)
    latest_elo: Mapped[float] = mapped_column(Numeric(precision=10, scale=6), nullable=False,
                                              server_default='1100.0', default=0)
    latest_wins: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    latest_losses: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    latest_drp: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)

    main_character: Mapped['CharacterList'] = relationship('CharacterList', lazy='joined')

    __table_args__ = (
        Index('idx_users_id', id),
        Index('idx_users_cc', cc),
        Index('idx_users_slippi_id', slippi_id)
    )

    def __repr__(self):
        return f'User({self.id}, "{self.cc}", "{self.name}", {self.main_id}("{self.main_character.name}"), ' \
               f'{self.slippi_id}, {self.latest_elo}, ({self.latest_wins}/{self.latest_losses}) )'


class CharacterList(Base):
    __tablename__ = 'character_list'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    character_entries: Mapped[list['CharactersEntry']] = relationship('CharactersEntry',
                                                                      back_populates='character_info',
                                                                      lazy='select')


class EntryDate(Base):
    __tablename__ = 'entry_date'

    entry_time: Mapped[datetime] = mapped_column(DateTime, primary_key=True, default=datetime.utcnow())


class Elo(Base):
    __tablename__ = 'elo'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    elo: Mapped[float] = mapped_column(Numeric(precision=10, scale=6), nullable=False, server_default='0.0', default=0)
    entry_time: Mapped[datetime] = mapped_column(DateTime, ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        Index('idx_elo_user_id', user_id),
        Index('idx_elo_entry_time', entry_time)
    )


class WinLoss(Base):
    __tablename__ = 'win_loss'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    entry_time: Mapped[datetime] = mapped_column(DateTime, ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        Index('idx_win_loss_user_id', user_id),
        Index('idx_win_loss_entry_time', entry_time)
    )


class DRP(Base):
    __tablename__ = 'daily_regional_placement'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    placement: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    entry_time: Mapped[datetime] = mapped_column(DateTime, ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        Index('idx_daily_regional_placement_user_id', user_id),
        Index('idx_daily_regional_placement_entry_time', entry_time)
    )


class DGP(Base):
    __tablename__ = 'daily_global_placement'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    placement: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    entry_time: Mapped[datetime] = mapped_column(DateTime, ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        Index('idx_daily_global_placement_user_id', user_id),
        Index('idx_daily_global_placement_entry_time', entry_time)
    )


class Leaderboard(Base):
    __tablename__ = 'leaderboard'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    elo: Mapped[float] = mapped_column(Numeric(precision=10, scale=6), nullable=False, server_default='0.0', default=0)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    entry_time: Mapped[datetime] = mapped_column(DateTime, ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        Index('idx_leaderboard_user_id', user_id),
        Index('idx_leaderboard_entry_time', entry_time)
    )


class CharactersEntry(Base):
    __tablename__ = 'character_entry'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey('character_list.id'), nullable=False)
    game_count: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime, ForeignKey('entry_date.entry_time'), nullable=False)

    character_info: Mapped['CharacterList'] = relationship('CharacterList',
                                                           back_populates='character_entries', lazy='joined')

    __table_args__ = (
        Index('idx_character_entry_user_id', user_id),
        Index('idx_character_entry_entry_time', entry_time)
    )


def generate_latest_entry(model):
    return (
        select(model.user_id, func.max(model.entry_time).label('max_entry_time'))
        .group_by(model.user_id)
        .alias()
        )


def get_leaderboard_between():
    start_datetime = datetime(2022, 1, 1)
    end_datetime = datetime(2024, 1, 1)

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
            session.query(User.id, User.name, Elo.elo, WinLoss.wins, WinLoss.losses, DRP.placement, Elo.entry_time)
            .join(latest_elo, latest_elo.c.user_id == User.id)
            .join(Elo, and_(Elo.user_id == latest_elo.c.user_id, Elo.entry_time == latest_elo.c.max_entry_time))
            .outerjoin(latest_win_losses, latest_win_losses.c.user_id == User.id)
            .outerjoin(WinLoss, and_(WinLoss.user_id == latest_win_losses.c.user_id,
                                     WinLoss.entry_time == latest_win_losses.c.max_entry_time))
            .outerjoin(latest_drp, latest_drp.c.user_id == User.id)
            .outerjoin(DRP, and_(DRP.user_id == latest_drp.c.user_id, DRP.entry_time == latest_drp.c.max_entry_time))
            .order_by(Elo.elo.desc())
        )

        print(query)

        return_value = session.execute(query).fetchall()
        return return_value


def get_users_leaderboard_correct():


    leaderboard_text = []
    counter = 1
    with create_session() as session:
        leaderboard = session.query(
            User.id,
            User.cc,
            User.name,
            User.latest_wins,
            User.latest_losses,
            Elo.elo,
            Elo.entry_time).\
            join(Elo, User.id == Elo.user_id).\
            filter(Elo.entry_time == session.query(func.max(Elo.entry_time)).
                   filter(Elo.user_id == User.id).scalar()).order_by(Elo.elo.desc()).\
            all()

        for entry in leaderboard:
            if entry[3] != 1100:
                leaderboard_text.append(f'{counter}. '
                                        f'{entry[2]} | '
                                        f'{entry[5]}'
                                        f'({entry[3]}/{entry[4]}) '
                                        f'{get_rank(entry[5])}')

    return leaderboard_text


def get_users_leaderboard():
    leaderboard_text = []
    counter = 1
    with create_session() as session:
        users = session.query(User).order_by(User.latest_elo.desc()).all()
        for user in users:
            if user.latest_elo != 1100:
                leaderboard_text.append(f'{counter}. {user.name} | {user.latest_elo:.2f} '
                                        f'({user.latest_wins}/{user.latest_losses}) {get_rank(user.latest_elo)}')
                counter += 1

    return leaderboard_text


def create_character_list():

    with create_session() as session:
        # Create CharacterList with entries from SlippiCharacterId
        # Because 0 is used for DK, we are mapping 0 to 255
        print(len(session.query(CharacterList).all()))
        if len(session.query(CharacterList).all()) != 27:
            for key, value in SlippiCharacterId.items():
                # DK claus
                if value == 0:
                    value = 255
                session.add(CharacterList(id=value, name=key))

            session.commit()


def initialize():
    with create_session() as session:
        # Create the tables in the database
        Base.metadata.create_all(engine)


    # session.add(User(name='test_user'))
    # session.add(Characters(user_id=1, character_id=1))

    #for i in range(50000):
    #    random_character_id = random.randint(1, 26)
    #    session.add(CharactersEntry(user_id=1, character_id=2, game_count=10, entry_time='2023-04-20 16:51:55'))

        session.commit()

    create_character_list()
