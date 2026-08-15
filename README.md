#  Story Dice AI Creative Story Generator

[![AWS Serverless](https://img.shields.io/badge/AWS-Serverless-orange.svg)](https://aws.amazon.com/)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock%20Nova-blue.svg)](https://aws.amazon.com/bedrock/)
[![AWS Amplify](https://img.shields.io/badge/Hosted%20on-AWS%20Amplify-FF9900.svg)](https://aws.amazon.com/amplify/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An interactive, whimsical story generation web app built for the **AWS Builder Weekend Challenge: Build a Creative App** (August 14–17, 2026).

Roll 4 virtual dice (**Place**, **Object**, **Trait**, and **Twist**) and let **Amazon Bedrock (Nova Micro)** weave them into a 150–200 word flash fiction story. Save your favorite stories directly to **Amazon DynamoDB**.

---

##  Live Demo & Links

- **Live Application**: [https://main.d248s959nwwhyo.amplifyapp.com/](https://main.d248s959nwwhyo.amplifyapp.com/)

---

##  Architecture Overview


```

[ Frontend: HTML / CSS / JS ] (AWS Amplify)
|
v
[ Amazon API Gateway ]
|
+----------+----------+----------+
|          |          |          |
v          v          v          v
/roll    /generate    /save    /stories  (AWS Lambda - Python 3.12)
|          |          |
v          +----+-----+
[Amazon Bedrock]       |
(Nova Micro)           v
            [Amazon DynamoDB]

```

### AWS Services Used
- **Amazon Bedrock (`amazon.nova-micro-v1:0`)**: Foundation model for generative storytelling.
- **AWS Lambda**: Serverless microservice compute.
- **Amazon API Gateway**: HTTP API routing and endpoint management.
- **Amazon DynamoDB**: NoSQL database for saved story collections.
- **AWS Amplify Hosting**: Continuous deployment and global CDN web hosting.
- **AWS SAM**: Infrastructure as Code (IaC) deployment.

---

## Project Structure

```text
.
├── backend/
│   ├── generate/       # Invokes Amazon Bedrock Nova Micro
│   ├── roll/           # Returns randomized dice attributes
│   ├── save/           # Persists generated stories to DynamoDB
│   ├── stories/        # Fetches saved story list
│   └── template.yaml   # AWS SAM Infrastructure as Code template
├── frontend/
│   ├── app.js          # UI interaction & API calls
│   ├── config.js       # API Gateway base URL & configuration
│   ├── index.html      # Main application interface
│   └── styles.css      # Styling and dice roll animations
├── amplify.yml         # AWS Amplify hosting configuration
└── README.md

```

---

## Local Development & Deployment

### 1. Deploy Backend via AWS SAM

```bash
cd backend
sam build
sam deploy --guided

```

### 2. Configure Frontend

Update `frontend/config.js`:

```javascript
const CONFIG = {
    USE_MOCK: false,
    API_BASE_URL: "https://<your-api-gateway-id>[.execute-api.us-east-1.amazonaws.com/prod](https://.execute-api.us-east-1.amazonaws.com/prod)"
};

```

### 3. Deploy Frontend with AWS Amplify

1. Push changes to GitHub.
2. Connect the repository in AWS Amplify Console.
3. Amplify will auto-detect `amplify.yml` and deploy the static website.

---

## License

This project is open-source under the MIT License.
