import configparser
import csv
from itertools import combinations
import logging
import pickle
import os

logger = logging.getLogger(__name__)


def all_combinations(*args):
    """
    Creates all combinations of an iterable of arguments

    args
        any iterable sequence

    returns
        combinations (list)
    """
    combos = []
    #  to get all combinations of any size we iterate over the range of
    #  lengths for each combination
    for length in range(1, len(args)+1):

        #  create all combinations of a given length
        for combo in combinations(args, length):
            combos.append(combo)

    return combos


def ensure_dir(file_path):
    """
    Checks a directory exists.  If it doesn't - makes it.

    args
        file_path (str)
    """
    directory = os.path.dirname(file_path)

    if not os.path.exists(directory):
        os.makedirs(directory)


def parse_ini(filepath, section):
    """
    Reads a single ini file

    args
        filepath (str) location of the .ini
        section (str) section of the ini to read

    returns
        config_dict (dict)

    Also converts boolean arguments from str to bool
    """
    logger.info('reading {}'.format(filepath))
    config = configparser.ConfigParser()
    config.read(filepath)

    #  check to convert boolean strings to real booleans
    config_dict = dict(config[section])

    for k, val in config_dict.items():
        if val == 'True':
            config_dict[k] = True

        if val == 'False':
            config_dict[k] = False

    return config_dict


def dump_pickle(obj, name):
    """
    Saves an object to a pickle file.

    args
        obj (object)
        name (str) path of the dumped file
    """
    with open(name, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle(name):
    """
    Loads a an object from a pickle file.

    args
        name (str) path to file to be loaded

    returns
        obj (object)
    """
    with open(name, 'rb') as handle:
        return pickle.load(handle)


def save_args(config, path):
    """ saves a config dictionary to a text file """
    with open(path, 'w') as outfile:
        writer = csv.writer(outfile)

        for k, v in config.items():
            logger.debug('{} : {}'.format(k, v))
            writer.writerow([k]+[v])


def load_args(path, drop=True):
    """ loads a dictionary from a text file """
    with open(path, 'r') as args:
        lines = {line.split(',')[0]: line.split(',')[1][:-1]
                 for line in args.readlines()}

        if drop:
            drop_args = [
                'act_path', 'learn_path', 'sess', 'env_repr',
            ]

            [lines.pop(key, None) for key in drop_args]

            return lines


def test_index_length(df, freq):
    test_idx = pd.DatetimeIndex(
        start=df.index[0],
        end=df.index[-1],
        freq=freq
    )
    assert test_idx.shape[0] == df.shape[0]


def read_iterable_from_config(argument):
    if isinstance(argument, str):
        argument = argument.split(',')
        argument = [int(argument) for argument in argument]
    else:
        argument = tuple(argument)

    return argument
