from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_logs as logs,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_stepfunctions as sfn,
    RemovalPolicy
)
from constructs import Construct

class Day01Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        queue = sqs.Queue(
            self, "Queue",
            visibility_timeout=Duration.seconds(300),
        )

        # ---------------------------------------------------------------------
        # 1. MONITORING SETUP: CloudWatch Logs & SNS Notification Topic
        # ---------------------------------------------------------------------

        # Log group for Step Functions Execution history
        log_group = logs.LogGroup(
            self, "StateMachineLogGroup",
            log_group_name="/aws/vendedlogs/states/StepFunctionsDemo-Logs",
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY  # Change for production
        )

        # SNS Alert Topic for execution failures
        error_topic = sns.Topic(
            self, "StateMachineErrorTopic",
            display_name="Step Function Execution Failure Alerts",
            topic_name="sf-execution-failure-topic"
        )

        # Example subscription (Replace with your actual email)
        error_topic.add_subscription(
            subscriptions.EmailSubscription("hum.tum.8765@gmail.com")
        )

        # ---------------------------------------------------------------------
        # 2. STEP FUNCTION DEFINITION
        # ---------------------------------------------------------------------

        # Define a simple Pass State that processes some dummy data
        start_state = sfn.Pass(
            self, "WelcomeState",
            result=sfn.Result.from_object({
                "status": "Success",
                "message": "Hello from AWS CDK!"
            })
        )

        # Define the State Machine
        state_machine = sfn.StateMachine(
            self, "MySimpleStateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(start_state),
            state_machine_type=sfn.StateMachineType.STANDARD,

            # Enable AWS X-Ray Tracing
            tracing_enabled=True,

            # Enable Detailed CloudWatch Logging
            logs=sfn.LogOptions(
                destination=log_group,
                level=sfn.LogLevel.ALL,
                include_execution_data=True
            )
        )
