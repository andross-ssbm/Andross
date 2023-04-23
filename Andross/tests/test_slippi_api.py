from Andross.slippi.slippi_api import connect_code_to_html, is_valid_connect_code, __get_player_data, \
    get_player_ranked_data, does_exist


def test_connect_code_to_html():
    assert connect_code_to_html('ABCD#1234') == 'ABCD-1234'
    assert connect_code_to_html('PXYZ#0987') == 'PXYZ-0987'
    assert connect_code_to_html('EFGH#4567') == 'EFGH-4567'


def test_is_valid_connect_code():
    assert is_valid_connect_code('ABCD#1234')
    assert is_valid_connect_code('ABCDEFG#0')
    assert is_valid_connect_code('A#0')
    assert is_valid_connect_code('A#1234567')
    assert not is_valid_connect_code('ABCDEFGH#1234567')
    assert not is_valid_connect_code('ABCDEFGH#0')
    assert not is_valid_connect_code('A#12345678')
    assert not is_valid_connect_code('ABC123')


def test_get_player_data():
    code = 'SO#0'
    results = __get_player_data(code)
    # Check if things exists
    assert results
    assert results['data']
    assert results['data']['getConnectCode']
    assert results['data']['getConnectCode']['user']

    # Check users for specific values
    user = results['data']['getConnectCode']['user']
    assert user['connectCode']['code'] == 'SO#0'
    assert user['rankedNetplayProfile']
    assert user['rankedNetplayProfile']['wins']
    assert user['rankedNetplayProfile']['losses']
    assert user['rankedNetplayProfile']['characters']

    # Check for nonexistent user
    code = 'ABCDEFG#0'
    results = __get_player_data(code)
    # Check if things exist
    assert results
    assert results['data']
    assert not results['data']['getConnectCode']

    # Check for invalid connect code
    code = 'abcdef'
    results = __get_player_data(code)
    assert not results


def test_get_player_ranked_data():
    results = get_player_ranked_data('so#0')
    assert results
    results = get_player_ranked_data('abcde')
    assert not results


def test_does_exist():
    assert does_exist('so#0')
    assert not does_exist('abcde')
