import csv
from datetime import datetime, timedelta


from tqdm import tqdm

from zoneinfo import ZoneInfo

from Andross.database.models import create_session, User, EntryDate, Elo, WinLoss, Leaderboard, DRP, DGP, \
    CharactersEntry
from Andross.database.queries import get_writeable_before_leaderboard

cvs_files = [
    'users.csv',
    'date.csv',
    'rank.csv',
    'elo.csv',
    'win_loss.csv'
]

with create_session() as session:
    print(f'Writing: {cvs_files[0]}')
    with open(f'data_export_test/{cvs_files[0]}', newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for row in tqdm(reader):
            session.add(User(id=int(row[0]),
                             cc=row[2],
                             name=row[1]
                             ))
            session.commit()

    print(f'Writing: {cvs_files[1]}')
    with open(f'data_export_test/{cvs_files[1]}', newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for row in tqdm(reader):
            session.add(EntryDate(entry_time=datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f').replace(microsecond=0)))
            session.commit()

    print(f'Writing: {cvs_files[3]}')
    with open(f'data_export_test/{cvs_files[3]}', newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for row in tqdm(reader):
            date = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f').replace(microsecond=0)
            session.add(Elo(user_id=int(row[0]),
                            elo=float(row[2]),
                            entry_time=date))
            session.commit()

    print(f'Writing: {cvs_files[4]}')
    with open(f'data_export_test/{cvs_files[4]}', newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for row in tqdm(reader):
            date = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f').replace(microsecond=0)
            session.add(WinLoss(
                user_id=int(row[0]),
                wins=int(row[1]),
                losses=int(row[2]),
                entry_time=date
            ))
            session.commit()

    print(f'Deleting non unique Elo')
    for guy in session.query(User).all():
        print(f'Deleting non unique elo entries for {guy.name}')
        latest_unique_elo = 0
        for elo_entry in tqdm(session.query(Elo).filter(Elo.user_id == guy.id).all()):
            if abs(elo_entry.elo - latest_unique_elo) < 0.1 or elo_entry.elo == 0 or elo_entry.elo == 1100:
                session.query(Elo).filter(Elo.id == elo_entry.id).delete()
                session.commit()
            else:
                latest_unique_elo = elo_entry.elo

    print('Deleting non unique WinLoss')
    for guy in session.query(User).all():
        print(f'Deleting non unique win/loss entries for {guy.name}')
        latest_unique_wins = 0
        latest_unique_losses = 0
        for wins_loss_entry in tqdm(session.query(WinLoss).filter(WinLoss.user_id == guy.id).all()):
            if wins_loss_entry.wins == latest_unique_wins and wins_loss_entry.losses == latest_unique_losses:
                session.query(WinLoss).filter(WinLoss.id == wins_loss_entry.id).delete()
                session.commit()
            else:
                latest_unique_wins = wins_loss_entry.wins
                latest_unique_losses = wins_loss_entry.losses

    print('Create a entry date for each day at midnight')
    # Set up the timezone objects for Eastern Time (US & Canada) and UTC
    est_tz = ZoneInfo('America/New_York')
    utc_tz = ZoneInfo('UTC')

    # Loop through each month in 2023
    for month in range(1, 5):
        # Get the first day of the month
        date = datetime(2023, month, 1, 23, 59, tzinfo=est_tz)

        # Loop through each day in the month
        while date.month == month and (date.month != datetime.utcnow().month and date.day != datetime.utcnow()):
            # Convert the date to UTC
            utc_date = date.astimezone(utc_tz)

            # Print the date in the desired format
            utc_time_to_write = utc_date.strftime('%Y-%m-%d %H:%M:%S')
            print(utc_time_to_write)
            session.add(EntryDate(
                entry_time=utc_date.replace(microsecond=0, tzinfo=None)
            ))
            session.commit()
            counter = 1
            for placements in get_writeable_before_leaderboard(utc_date.replace(microsecond=0, tzinfo=None))[1]:
                session.add(Leaderboard(
                    user_id=placements[0],
                    position=counter,
                    elo=placements[1],
                    wins=placements[2],
                    losses=placements[3],
                    drp=placements[4],
                    entry_time=utc_date.replace(microsecond=0, tzinfo=None)
                ))
                session.commit()
                counter += 1
            # Move to the next day
            date += timedelta(days=1)

    print('Removing redundant dates')
    # Remove redundant dates
    for dates in tqdm(session.query(EntryDate).order_by(EntryDate.entry_time.asc()).all()):
        has_data = False
        # Check Elo
        if session.query(Elo).filter(Elo.entry_time == dates.entry_time).all():
            has_data = True
        # Check win_loss
        if session.query(WinLoss).filter(WinLoss.entry_time == dates.entry_time).all():
            has_data = True
        # Check daily_regional_placement
        if session.query(DRP).filter(DRP.entry_time == dates.entry_time).all():
            has_data = True
        # Check daily_global_placement
        if session.query(DGP).filter(DGP.entry_time == dates.entry_time).all():
            has_data = True
        # Check character_entry
        if session.query(CharactersEntry).filter(CharactersEntry.entry_time == dates.entry_time).all():
            has_data = True
        # Check leaderboard
        if session.query(Leaderboard).filter(Leaderboard.entry_time == dates.entry_time).all():
            has_data = True
        # Remove date
        if has_data:
            session.query(EntryDate).filter(EntryDate == dates.entry_time).delete()
