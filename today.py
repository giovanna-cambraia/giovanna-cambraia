import datetime
import hashlib
import os
import time
from dateutil import relativedelta
from lxml import etree
import requests

# Fine-grained personal access token with All Repositories access:
# Repository permissions: read:Commit statuses, read:Contents, read:Issues, read:Metadata, read:Pull Requests
HEADERS = {'authorization': 'token ' + os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']
QUERY_COUNT = {
    'user_getter': 0,
    'graph_repos_stars': 0,
    'recursive_loc': 0,
    'graph_commits': 0,
    'loc_query': 0,
}


def daily_readme(birthday):
    """Returns the length of time since birthday, e.g. 'XX years, XX months, XX days'."""
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years,
        'year' + format_plural(diff.years),
        diff.months,
        'month' + format_plural(diff.months),
        diff.days,
        'day' + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else '',
    )


def format_plural(unit):
    return 's' if unit != 1 else ''


def simple_request(func_name, query, variables):
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS,
    )
    if response.status_code == 200:
        return response
    raise Exception(
        f'{func_name} has failed with a {response.status_code}: {response.text}',
        QUERY_COUNT,
    )


def graph_commits(start_date, end_date):
    query_count('graph_commits')
    query = '''
    query($start_date: DateTime!, $end_date: DateTime!, $login: String!) {
        user(login: $login) {
            contributionsCollection(from: $start_date, to: $end_date) {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }'''
    variables = {'start_date': start_date, 'end_date': end_date, 'login': USER_NAME}
    res = simple_request(graph_commits.__name__, query, variables)
    return int(
        res.json()['data']['user']['contributionsCollection']['contributionCalendar'][
            'totalContributions'
        ]
    )


def graph_repos_stars(count_type, owner_affiliation, cursor=None):
    query_count('graph_repos_stars')
    query = '''
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: $owner_affiliation) {
                totalCount
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }'''
    variables = {
        'owner_affiliation': owner_affiliation,
        'login': USER_NAME,
        'cursor': cursor,
    }
    res = simple_request(graph_repos_stars.__name__, query, variables)
    if count_type == 'repos':
        return res.json()['data']['user']['repositories']['totalCount']
    raise ValueError(f'Unsupported count_type: {count_type}')


def recursive_loc(
    owner,
    repo_name,
    data,
    cache_comment,
    addition_total=0,
    deletion_total=0,
    my_commits=0,
    cursor=None,
):
    query_count('recursive_loc')
    query = '''
    query ($repo_name: String!, $owner: String!, $cursor: String) {
        repository(name: $repo_name, owner: $owner) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100, after: $cursor) {
                            totalCount
                            edges {
                                node {
                                    ... on Commit {
                                        committedDate
                                    }
                                    author {
                                        user {
                                            id
                                        }
                                    }
                                    deletions
                                    additions
                                }
                            }
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                        }
                    }
                }
            }
        }
    }'''
    variables = {'repo_name': repo_name, 'owner': owner, 'cursor': cursor}
    request = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS,
    )
    if request.status_code == 200:
        default_branch = request.json()['data']['repository']['defaultBranchRef']
        if default_branch is not None:
            return loc_counter_one_repo(
                owner,
                repo_name,
                data,
                cache_comment,
                default_branch['target']['history'],
                addition_total,
                deletion_total,
                my_commits,
            )
        return 0, 0, 0

    force_close_file(data, cache_comment)
    if request.status_code == 403:
        raise Exception(
            "Too many requests in a short amount of time!\nYou've hit the non-documented anti-abuse limit!"
        )
    raise Exception(
        'recursive_loc() has failed with a',
        request.status_code,
        request.text,
        QUERY_COUNT,
    )


def loc_counter_one_repo(
    owner,
    repo_name,
    data,
    cache_comment,
    history,
    addition_total,
    deletion_total,
    my_commits,
):
    for edge in history['edges']:
        node = edge['node']
        author_user = node.get('author', {}).get('user')
        if author_user and author_user.get('id') == OWNER_ID:
            my_commits += 1
            addition_total += node['additions']
            deletion_total += node['deletions']

    if not history['edges'] or not history['pageInfo']['hasNextPage']:
        return addition_total, deletion_total, my_commits
    return recursive_loc(
        owner,
        repo_name,
        data,
        cache_comment,
        addition_total,
        deletion_total,
        my_commits,
        history['pageInfo']['endCursor'],
    )


def loc_query(
    owner_affiliation, comment_size=0, force_cache=False, cursor=None, edges=None
):
    if edges is None:
        edges = []
    query_count('loc_query')
    query = '''
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 60, after: $cursor, ownerAffiliations: $owner_affiliation) {
                edges {
                    node {
                        ... on Repository {
                            nameWithOwner
                            defaultBranchRef {
                                target {
                                    ... on Commit {
                                        history {
                                            totalCount
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }'''
    variables = {
        'owner_affiliation': owner_affiliation,
        'login': USER_NAME,
        'cursor': cursor,
    }
    res = simple_request(loc_query.__name__, query, variables)
    repos_data = res.json()['data']['user']['repositories']
    edges.extend(repos_data['edges'])
    if repos_data['pageInfo']['hasNextPage']:
        return loc_query(
            owner_affiliation,
            comment_size,
            force_cache,
            repos_data['pageInfo']['endCursor'],
            edges,
        )
    return cache_builder(edges, comment_size, force_cache)


def cache_builder(edges, comment_size, force_cache, loc_add=0, loc_del=0):
    cached = True
    os.makedirs('cache', exist_ok=True)
    filename = f"cache/{hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest()}.txt"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.readlines()
    except FileNotFoundError:
        data = [
            'This line is a comment block. Write whatever you want here.\n'
            for _ in range(comment_size)
        ]
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(data)

    if len(data) - comment_size != len(edges) or force_cache:
        cached = False
        flush_cache(edges, filename, comment_size)
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.readlines()

    cache_comment = data[:comment_size]
    data = data[comment_size:]
    for index, edge in enumerate(edges):
        repo_hash, commit_count, *__ = data[index].split()
        name_with_owner = edge['node']['nameWithOwner']
        expected_hash = hashlib.sha256(name_with_owner.encode('utf-8')).hexdigest()
        if repo_hash == expected_hash:
            try:
                total_commits = edge['node']['defaultBranchRef']['target']['history'][
                    'totalCount'
                ]
                if int(commit_count) != total_commits:
                    owner, repo_name = name_with_owner.split('/')
                    loc = recursive_loc(owner, repo_name, data, cache_comment)
                    data[index] = (
                        f'{repo_hash} {total_commits} {loc[2]} {loc[0]} {loc[1]}\n'
                    )
            except TypeError:
                data[index] = f'{repo_hash} 0 0 0 0\n'

    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(cache_comment)
        f.writelines(data)

    for line in data:
        parts = line.split()
        loc_add += int(parts[3])
        loc_del += int(parts[4])

    return [loc_add, loc_del, loc_add - loc_del, cached]


def flush_cache(edges, filename, comment_size):
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.readlines()[:comment_size] if comment_size > 0 else []
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(data)
        for node in edges:
            repo_hash = hashlib.sha256(
                node['node']['nameWithOwner'].encode('utf-8')
            ).hexdigest()
            f.write(f'{repo_hash} 0 0 0 0\n')


def add_archive():
    with open('cache/repository_archive.txt', 'r', encoding='utf-8') as f:
        data = f.readlines()
    old_data = data
    data = data[7 : len(data) - 3]
    added_loc, deleted_loc, added_commits = 0, 0, 0
    contributed_repos = len(data)
    for line in data:
        _, _, my_commits, *loc = line.split()
        added_loc += int(loc[0])
        deleted_loc += int(loc[1])
        if my_commits.isdigit():
            added_commits += int(my_commits)
    added_commits += int(old_data[-1].split()[4][:-1])
    return [
        added_loc,
        deleted_loc,
        added_loc - deleted_loc,
        added_commits,
        contributed_repos,
    ]


def force_close_file(data, cache_comment):
    filename = f"cache/{hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest()}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(cache_comment)
        f.writelines(data)
    print(
        f'There was an error while writing to the cache file. {filename} has had partial data saved.'
    )


def svg_overwrite(
    filename, age_data, commit_data, repo_data, contrib_data, loc_data
):
    tree = etree.parse(filename)
    root = tree.getroot()
    justify_format(root, 'age_data', age_data)
    justify_format(root, 'commit_data', commit_data, 22)
    justify_format(root, 'repo_data', repo_data, 6)
    justify_format(root, 'contrib_data', contrib_data)
    justify_format(root, 'loc_data', loc_data[2], 9)
    justify_format(root, 'loc_add', loc_data[0])
    justify_format(root, 'loc_del', loc_data[1], 7)
    tree.write(filename, encoding='utf-8', xml_declaration=True)


def justify_format(root, element_id, new_text, length=0):
    if isinstance(new_text, int):
        new_text = f'{new_text:,}'
    new_text = str(new_text)
    find_and_replace(root, element_id, new_text)
    just_len = max(0, length - len(new_text))
    if just_len <= 2:
        dot_map = {0: '', 1: ' ', 2: '. '}
        dot_string = dot_map[just_len]
    else:
        dot_string = ' ' + ('.' * just_len) + ' '
    find_and_replace(root, f'{element_id}_dots', dot_string)


def find_and_replace(root, element_id, new_text):
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = new_text


def commit_counter(comment_size):
    total_commits = 0
    filename = f"cache/{hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest()}.txt"
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.readlines()[comment_size:]
    for line in data:
        total_commits += int(line.split()[2])
    return total_commits


def user_getter(username):
    query_count('user_getter')
    query = '''
    query($login: String!){
        user(login: $login) {
            id
            createdAt
        }
    }'''
    res = simple_request(user_getter.__name__, query, {'login': username})
    user = res.json()['data']['user']
    return user['id'], user['createdAt']


def query_count(funct_id):
    QUERY_COUNT[funct_id] += 1


def perf_counter(funct, *args):
    start = time.perf_counter()
    funct_return = funct(*args)
    return funct_return, time.perf_counter() - start


def formatter(query_type, difference):
    print(f"{'   ' + query_type + ':':<23}", end='')
    if difference > 1:
        print(f'{difference:>11.4f} s ')
    else:
        print(f'{difference * 1000:>10.4f} ms')


if __name__ == '__main__':
    print('Calculation times:')
    (OWNER_ID, acc_date), user_time = perf_counter(user_getter, USER_NAME)
    formatter('account data', user_time)

    age_data, age_time = perf_counter(daily_readme, datetime.datetime(2002, 7, 5))
    formatter('age calculation', age_time)

    total_loc, loc_time = perf_counter(
        loc_query, ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'], 7
    )
    formatter('LOC (cached)' if total_loc[-1] else 'LOC (no cache)', loc_time)

    commit_data, commit_time = perf_counter(commit_counter, 7)
    repo_data, repo_time = perf_counter(graph_repos_stars, 'repos', ['OWNER'])
    contrib_data, contrib_time = perf_counter(
        graph_repos_stars, 'repos', ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER']
    )

    if OWNER_ID == 'MDQ6VXNlcjU3MzMxMTM0' and os.path.exists('cache/repository_archive.txt'):
        archived_data = add_archive()
        for index in range(len(total_loc) - 1):
            total_loc[index] += archived_data[index]
        contrib_data += archived_data[-1]
        commit_data += int(archived_data[-2])

    formatted_loc = [f'{val:,}' for val in total_loc[:-1]]

    for svg_file in ('dark_mode.svg', 'light_mode.svg'):
        if os.path.exists(svg_file):
            svg_overwrite(
                svg_file, age_data, commit_data, repo_data, contrib_data, formatted_loc
            )

    total_time = (
        user_time + age_time + loc_time + commit_time + repo_time + contrib_time
    )
    print(
        '\033[F\033[F\033[F\033[F\033[F\033[F',
        f"{'Total function time:':<21}{total_time:>11.4f} s ",
        '\033[E\033[E\033[E\033[E\033[E\033[E',
        sep='',
    )

    print('Total GitHub GraphQL API calls:', f'{sum(QUERY_COUNT.values()):>3}')
    for funct_name, count in QUERY_COUNT.items():
        print(f"{'   ' + funct_name + ':':<28}{count:>6}")