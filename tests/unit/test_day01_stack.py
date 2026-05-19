import aws_cdk as core
import aws_cdk.assertions as assertions

from day01.day01_stack import Day01Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in day01/day01_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Day01Stack(app, "day01")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
