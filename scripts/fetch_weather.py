import _bootstrap
import argparse
import logging
from src.config import TURBINES, local_date
from src.services.weather_provider import OpenMeteoProvider

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--start',default='2024-01-01')
    parser.add_argument('--end',default='2026-03-03')
    args=parser.parse_args()
    provider=OpenMeteoProvider()
    for turbine,cfg in TURBINES.items():
        frame=provider.archive_range(cfg['latitude'],cfg['longitude'],local_date(args.start),local_date(args.end))
        logging.info('%s: %s rows, missing=%s',turbine,len(frame),frame.isna().sum().to_dict())

if __name__=='__main__': main()
