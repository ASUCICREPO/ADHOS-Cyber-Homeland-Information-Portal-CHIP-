import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from 'aws-cdk-lib/aws-iam';
import { Duration } from 'aws-cdk-lib'
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import * as api_gateway from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';
import { RemovalPolicy } from 'aws-cdk-lib';
import * as kendra from 'aws-cdk-lib/aws-kendra';
import * as s3 from 'aws-cdk-lib/aws-s3';

require('dotenv').config()

// AWS Kendra index id
const kendra_index_id_ = process.env.AWS_KENDRA

const sender_address = process.env.SENDER_ADDRESS

const receiver_address = process.env.RECEIVER_ADDRESS

const access_key = process.env.ACCESS_KEY

const secret_access_key = process.env.SECRET_ACCESS_KEY


export class HomelanddemoStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps){
        super(scope, id, props);

 // S3 bucket for kendra source
 const myS3Bucket = new s3.Bucket(this, 'homelanddemo', {
  bucketName: "homelanddemobucket"
});

const Kendra_IAM_role = new iam.Role(this, 'kendra_index_role-demo', {
  assumedBy: new iam.ServicePrincipal('kendra.amazonaws.com')
});

Kendra_IAM_role.addToPolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: [
      "s3:*",
    ],
    resources: ["*"],
  })
)

 const Kendra_DataSource = new kendra.CfnDataSource(this, "Kendra_s3_connector-demo", {
  indexId: kendra_index_id_!,
  name: "homeland_datasource-demo",
  type: "S3",
  dataSourceConfiguration:{
    s3Configuration:{
      bucketName: myS3Bucket.bucketName
    }
  },
  description: "homeland-datasource-demo",
  roleArn: Kendra_IAM_role.roleArn
})

const langchain_layer = new lambda.LayerVersion(this, "HS-langchain_layer-demo", {
      compatibleRuntimes: [
        lambda.Runtime.PYTHON_3_10,
        lambda.Runtime.PYTHON_3_9,
        lambda.Runtime.PYTHON_3_8
      ],
      code: lambda.Code.fromAsset("layers/langchain"),
      description: 'The langchain layer with all dependencies',
    })

    // Lambda function created for the AWS Kendra retrieval and then chaining with the LLM to generate a response using the langchain layer
    const kendralangchain_func = new lambda.Function(this, "HS-kendralangchain-demo", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset("lambda"),
      handler: "KendraLangchain.handler",
      timeout: Duration.minutes(5),
      environment: {
        "AWS_KENDRA": kendra_index_id_!,
        "SENDER_ADDRESS": sender_address!,
        "RECEIVER_ADDRESS": receiver_address!,
        "ACCESS_KEY": access_key!,
        "SECRET_ACCESS_KEY": secret_access_key!
      },
      layers: [langchain_layer]
    });

    // providing IAM policy for the function
    kendralangchain_func.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "logs:*",
          "apigateway:*",
          "s3:*",
          "kendra:*",
          "bedrock:*"
        ],
        resources: ["*"],
      })
    )

    // API for the user management
    const api_created = new api_gateway.RestApi(this, 'HS-llm_generate_api-demo', {
      cloudWatchRole: true,
      deployOptions:{
        accessLogDestination: new api_gateway.LogGroupLogDestination(new logs.LogGroup(this, "HS-llm_generate_api_log_group", {
          logGroupName: "HS-llm_generate_api_log_group-demo",
          retention: RetentionDays.ONE_MONTH,
          removalPolicy: RemovalPolicy.DESTROY,
        })),
      }
    })
    // llm generator integration
    const llm_generator_integration = new api_gateway.LambdaIntegration(kendralangchain_func);

    // declaring the resource and then adding method 
    const llm_generation_api_path = api_created.root.addResource('generatellmdev')

    // adding post method
    llm_generation_api_path.addMethod("POST", llm_generator_integration)

    const send_email_api_path = api_created.root.addResource('sendemail')

    // adding post method for email integration
    send_email_api_path.addMethod("POST", llm_generator_integration)
  }
}