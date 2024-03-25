import boto3

import sys

# Define the certificate ARN template
CERTIFICATE_ARN = 'arn:aws:acm:{aws_region}:{account_id}:certificate/{certificate_arn}'

class CertificateFetcher:

    def __init__(self, environment, aws_region="us-east-1") -> None:
        self.aws_region = aws_region

        self.account_id = ''
        self.fetcher_certificate_arn = ''

        # Initialize boto3 clients for the specified region
        self.elbv2_client = boto3.client('elbv2', region_name=self.aws_region)
        self.elb_client = boto3.client('elb', region_name=self.aws_region)
        self.cloudfront_client = boto3.client('cloudfront', region_name=self.aws_region)
        self.apprunner_client = boto3.client('apprunner', region_name=self.aws_region)
        self.elasticbeanstalk_client = boto3.client('elasticbeanstalk', region_name=self.aws_region)

        match environment:
            case "staging":
                self.account_id = '589470546847'
            case "production":
                self.account_id = '114712639188'
            case _:
                print(f"There is no such environment available with this naming - {environment}.")
                sys.exit(1)

    def set_fetcher_certificate_arn(self, certificate_arn="", domain_name=""):
        if certificate_arn:
            self.fetcher_certificate_arn = CERTIFICATE_ARN.format(aws_region=self.aws_region, account_id=self.account_id, certificate_arn=certificate_arn)
        elif domain_name:
            self.fetcher_certificate_arn = self.get_certificate_arn_by_domain_name(domain_name)
            if not self.fetcher_certificate_arn:
                print(f"Certificate with relevant DNS domain name failed to retrieve.")
                sys.exit(1)
        else:
            print(f"Failed to retrieve correct certificate arn.")
            sys.exit(1)
        
        print(f"Certificate arn to be checked - {self.fetcher_certificate_arn}")

    def check_classic_load_balancers(self):
        print("Checking Classic ELB listeners...")
        marker = None
        while True:
            if marker:
                response = self.elb_client.describe_load_balancers(Marker=marker)
            else:
                response = self.elb_client.describe_load_balancers()

            load_balancers = response['LoadBalancerDescriptions']
            for lb in load_balancers:
                for listener_description in lb['ListenerDescriptions']:
                    listener = listener_description['Listener']
                    if 'SSLCertificateId' in listener:
                        cert_arn = listener['SSLCertificateId']
                        if cert_arn == self.fetcher_certificate_arn:
                            print(f"Certificate used in Classic ELB listener on port {listener['LoadBalancerPort']} for load balancer: {lb['LoadBalancerName']}")

            # Check if there's a NextMarker, which indicates more load balancers to list
            marker = response.get('NextMarker')
            if not marker:
                break

    def check_elbv2_listeners(self):
        print("Checking ALBs and NLBs listeners...")
        paginator = self.elbv2_client.get_paginator('describe_load_balancers')
        for page in paginator.paginate():
            for lb in page['LoadBalancers']:
                listeners_paginator = self.elbv2_client.get_paginator('describe_listeners')
                for listener_page in listeners_paginator.paginate(LoadBalancerArn=lb['LoadBalancerArn']):
                    for listener in listener_page['Listeners']:
                        for cert in listener.get('Certificates', []):
                            if cert['CertificateArn'] == self.fetcher_certificate_arn:
                                print(f"Certificate used in ELBv2 listener: {listener['ListenerArn']} on load balancer: {lb['LoadBalancerArn']}")

    def check_cloudfront_distributions(self):
        print("Checking Cloudfront distribution lists...")
        paginator = self.cloudfront_client.get_paginator('list_distributions')
        for page in paginator.paginate():
            if 'Items' in page['DistributionList']:
                for distribution in page['DistributionList']['Items']:
                    if distribution['ViewerCertificate'].get('ACMCertificateArn') == self.fetcher_certificate_arn:
                        print(f"Certificate used in CloudFront distribution: {distribution['Id']} with domain name: {distribution['DomainName']}")

    def check_apprunner_services(self):
        print("Checking AppRunner services...")
        next_token = None
        while True:
            # Describe service to get detailed information including custom domains
            if next_token:
                response = self.apprunner_client.list_services(NextToken=next_token)
            else:
                response = self.apprunner_client.list_services()

            services = response['ServiceSummaryList']
            for service in services:
                service_arn = service['ServiceArn']
                service_response = self.apprunner_client.describe_service(ServiceArn=service_arn)
                custom_domains = service_response['Service'].get('CustomDomains', [])
                for domain in custom_domains:
                    # Check if the associated certificate matches the one we're looking for
                    if domain['CertificateValidationRecords'][0]['Status'] == 'SUCCESS':
                        associated_cert_arn = domain.get('CertificateArn')
                        if associated_cert_arn == CERTIFICATE_ARN:
                            print(f"Certificate used in App Runner service: {service_arn} for domain {domain['DomainName']}")

            # Check if there's more services to list
            next_token = response.get('NextToken')
            if not next_token:
                break

    def check_elastic_beanstalk_environments(self):
        print("Checking Elastic Beanstalk environments...")
        paginator = self.elasticbeanstalk_client.get_paginator('describe_environments')
        for page in paginator.paginate():
            environments = page['Environments']
            for env in environments:
                env_name = env['EnvironmentName']
                settings_response = self.elasticbeanstalk_client.describe_configuration_settings(
                    ApplicationName=env['ApplicationName'],
                    EnvironmentName=env_name
                )
                option_settings = settings_response['ConfigurationSettings'][0]['OptionSettings']
                for setting in option_settings:
                    if setting['Namespace'] == 'aws:elbv2:listener:443' and setting['OptionName'] == 'SSLCertificateArns':
                        # Check if the SSLCertificateArns matches the certificate ARN
                        if setting['Value'] == self.fetcher_certificate_arn:
                            print(f"Certificate used in Elastic Beanstalk environment: {env_name}")
    
    def get_certificate_arn_by_domain_name(self, domain_name):
        acm_client = boto3.client('acm', region_name=self.aws_region)
        # List certificates with pagination
        paginator = acm_client.get_paginator('list_certificates')
        for page in paginator.paginate(CertificateStatuses=['ISSUED']):
            for cert_summary in page['CertificateSummaryList']:
                # Check if the certificate domain name matches the specified domain name
                if cert_summary['DomainName'] == domain_name:
                    # Return the certificate ARN
                    return cert_summary['CertificateArn']
        return None
