#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { HomelanddemoStack } from '../lib/homelanddemo-stack';

require('dotenv').config()

const envDev = {account: process.env.AWS_ACCOUNT, region: process.env.AWS_REGION }
const app = new cdk.App();
new HomelanddemoStack(app, 'HomelanddemoStack', {
  env: envDev,
  description: "Demo Env for Homeland"
});