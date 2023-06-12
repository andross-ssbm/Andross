import os
from datetime import datetime
import logging

from sqlalchemy import create_engine, Integer, BigInteger, \
    String, DateTime, Index, ForeignKey, func, and_, select, FLOAT, Double
from sqlalchemy.orm import relationship, DeclarativeBase, sessionmaker, Mapped, mapped_column, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from slippi.slippi_characters import SlippiCharacterId
from slippi.slippi_ranks import get_rank

# Database variables
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# create the database engine
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@'
                       f'{DB_HOST}:{DB_PORT}/{DB_NAME}', echo=False)


def create_session() -> Session:
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
    latest_elo: Mapped[float] = mapped_column(Double, nullable=False,
                                              server_default='1100.0', default=0)
    latest_wins: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    latest_losses: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    latest_drp: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)

    main_character: Mapped['CharacterList'] = relationship('CharacterList', lazy='joined')
    elo_entries: Mapped[list['Elo']] = relationship('Elo')
    win_loss_entries: Mapped[list['WinLoss']] = relationship('WinLoss')
    drp_entries: Mapped[list['DRP']] = relationship('DRP')
    dgp_entries: Mapped[list['DGP']] = relationship('DGP')
    characters_entries: Mapped[list['CharactersEntry']] = relationship('CharactersEntry')
    leaderboard_entries: Mapped[list['Leaderboard']] = relationship('Leaderboard')

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

    entry_time: Mapped[datetime] = mapped_column(DateTime, primary_key=True,
                                                 default=datetime.utcnow().replace(microsecond=0))


class Elo(Base):
    __tablename__ = 'elo'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)
    elo: Mapped[float] = mapped_column(Double, nullable=False, server_default='0.0', default=0)
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
    elo: Mapped[float] = mapped_column(Double, nullable=False,
                                       server_default='0.0', default=0)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
    drp: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0', default=0)
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


def create_character_list():

    with create_session() as session:
        # Create CharacterList with entries from SlippiCharacterId
        # Because 0 is used for DK, we are mapping 0 to 255
        if len(session.query(CharacterList).all()) != 27:
            for key, value in SlippiCharacterId.items():
                # DK claus
                if value == 0:
                    value = 255
                session.add(CharacterList(id=value, name=key))

            session.commit()


def initialize() -> bool:
    with create_session() as session:
        # Create the tables in the database
        Base.metadata.create_all(engine)

        session.commit()

    create_character_list()
    return True
