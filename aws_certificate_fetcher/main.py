import argparse
import sys

import fetcher

parser = argparse.ArgumentParser(description='CLI for AWSCertificateFetcher')

parser.add_argument('-a', '--arn', action="store", help="Provide an ACM certificate arn, to search it's usage among described AWS profile")
parser.add_argument('-e', '--environment', action="store", choices=['staging', 'production'], help="Which AWS environment to use for checking . Can be 'staging' or 'production' only")
parser.add_argument('-r', '--region', action="store", help="AWS Region, where ACM certificate defined, and where services can use this certificate")


args = parser.parse_args()

certificate_fetcher = fetcher.CertificateFetcher(args.arn, args.environment, args.region)

if not args.arn:
    print("To run the app you should specify the certificate arn from ACM, which needed to be checked accross the AWS infrastructure!")
    sys.exit(1)

certificate_fetcher.check_classic_load_balancers()
certificate_fetcher.check_elbv2_listeners()
# certificate_fetcher.check_cloudfront_distributions()
# certificate_fetcher.check_apprunner_services()
# certificate_fetcher.check_elastic_beanstalk_environments()
