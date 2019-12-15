import sys
import json
import jmespath
import pickle
import unittest
import warnings

from c7n.cli import main

# NOTE: requires an active AWS session because custodian cli does
AWS_PROFILE = 'redacted'
AWS_ACCOUNT = 'redacted'
AWS_REGION = 'us-east-1'


# region is validated in resource/aws.py so can't fake name (e.g. us-test-1)
# cache key structure from c7n query.py
def get_cache_key(resource, query):
    return {
        'account': AWS_ACCOUNT,
        'region': AWS_REGION,
        'resource': resource,
        'q': query
    }


def mock_cache(resource_type, resources_filename, cache_filename):
    with open(resources_filename) as f:
        resources = json.load(f)

    # c7n cache.py uses pickle for binary cache object format
    with open(cache_filename, 'wb') as f_cache:
        data = {}
        cache_key = get_cache_key(resource_type, None)
        data[pickle.dumps(cache_key)] = resources
        pickle.dump(data, f_cache, protocol=2)


def build_arv(custodian_policy, cache_filename):
    return ['custodian',
            'run',
            '--dryrun',
            '-s',
            'tmp',
            custodian_policy,
            '--profile',
            AWS_PROFILE,
            '--cache',
            cache_filename,
            '--region',
            AWS_REGION]


class TestElasticache(unittest.TestCase):
    CACHE_FILENAME = 'mock-cloud-custodian.cache'

    def setUp(self):
        # https://github.com/boto/boto3/issues/454
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*<ssl.SSLSocket.*>")

        # TODO: find alternative for backtick syntax since both generates PendingDeprecationWarning and doesn't work on jp cli
        # $cat elasticache-redis-insecure/resources.json | jp 'length([]."c7n:MatchedFilters"[?contains(@, `AuthTokenEnabled`)][])'
        # Error evaluating JMESPath expression: invalid character 'A' looking for beginning of value
        warnings.filterwarnings("ignore", category=PendingDeprecationWarning,
                                message="deprecated string literal syntax")

    def test_elasticache_insecure(self):

        mock_cache('ElastiCacheCluster', 'mock-elasticache-resources.json', self.CACHE_FILENAME)

        # TODO: instead or mocked cache, look at boto stubber
        # https://botocore.readthedocs.io/en/latest/reference/stubber.html

        tmp_argv = build_arv('elasticache-redis-insecure.yml', self.CACHE_FILENAME)
        sys.argv = tmp_argv

        main()

        with open('tmp/elasticache-redis-insecure/resources.json') as f:
            resources = json.load(f)

        count = jmespath.search('length([])', resources)
        self.assertEqual(4, count)

        count = jmespath.search('length([]."c7n:MatchedFilters"[?contains(@, `AuthTokenEnabled`)][])', resources)
        self.assertEqual(2, count)

        count = jmespath.search('length([]."c7n:MatchedFilters"[?contains(@, `TransitEncryptionEnabled`)][])',
                                resources)
        self.assertEqual(2, count)

        count = jmespath.search('length([]."c7n:MatchedFilters"[?contains(@, `AtRestEncryptionEnabled`)][])', resources)
        self.assertEqual(2, count)


if __name__ == '__main__':
    unittest.main()
