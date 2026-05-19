from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
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

        # ---------------------------------------------------------------------
        # 3. IAM POLICIES & SECURITY
        # ---------------------------------------------------------------------

        # CDK automatically builds minimal-privilege roles for Log Groups and X-Ray.
        # If an external service or Lambda needs to trigger this State Machine,
        # you can explicitly grant execution rights like this:

        trigger_role = iam.Role(
            self, "ExternalTriggerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        state_machine.grant_start_execution(trigger_role)

        # ---------------------------------------------------------------------
        # 4. CLOUDWATCH ALARMS & SNS ALERTS
        # ---------------------------------------------------------------------

        # Create a metric for failed executions
        failure_metric = state_machine.metric_failed(
            period=Duration.minutes(5),
            statistic="Sum"
        )

        # Trigger alarm if even 1 execution fails within a 5-minute window
        failure_alarm = cloudwatch.Alarm(
            self, "StateMachineFailureAlarm",
            metric=failure_metric,
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Alarm if the Step Function execution fails.",
            # critical_metric_alarm=True
        )

        # Link the Alarm to the SNS Topic
        failure_alarm.add_alarm_action(cw_actions.SnsAction(error_topic))
