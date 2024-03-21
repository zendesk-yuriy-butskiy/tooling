import argparse
import sys

import fetcher

parser = argparse.ArgumentParser(description='CLI for AWSCertificateFetcher')

parser.add_argument('--arn', action="store", help="Provide an ACM certificate arn, to search it's usage among described AWS profile")
parser.add_argument('--region', action="store", help="AWS Region, where ACM certificate defined, and where services can use this certificate")

args = parser.parse_args()

certificate_fetcher = fetcher.CertificateFetcher(args.arn, args.region)

if args.arn:
    certificate_fetcher.check_elbv2_listeners()
    certificate_fetcher.check_cloudfront_distributions()
    certificate_fetcher.check_apprunner_services()
    certificate_fetcher.check_elastic_beanstalk_environments()
else:
    print("To run the app you should specify the certificate arn from ACM, which needed to be checked accross the AWS infrastructure!")
    sys.exit(1)
