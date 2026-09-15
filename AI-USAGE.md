# AI USAGE 

## Part 1

1. Used AI Agent(ChatGPT) to browse through techniques for calculating SIGMA value dynamically through each feature per gateway.
    - The Technique suggested is Coefficient of Variation which calculates the Feature Variation based on the Feature Mean
    - This Calculated SIGMA values didn't vary from the base SIGMA value(only 2 to 4 features per 8 weeks varied from the base SIGMA in range of 0.1 to 0.3) 
2. Used for Understanding Logical Bugs while selecting Features based on Null Value Percentage in Correlation Pair selected from Correlation Threshold Function.

## Part 2(Machine Learning)

1. Used Microsoft Copilot to browse through suitable Unsupervised Machine Learning Algorithms for flagging Anomalies.
    - The Algorithm Suggested for Anomaly Detection is Isolation Forest for grading anomalies
    - I Selected Isolation Forest along with a density based algorithm 'Local Outlier Factor' and ranked the anomalies based on aggregated score of the two models
2. When Tried to read data from gateway_master.csv got the following error:

```bash
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xdf in position 161: invalid continuation byte
```

Used AI to Understand what caused the Issue and got to know some language characters are not usually identified by pandas so used **encoding="latin-1"** parameter to map non-ASCII characters i.e., German Characters to avoid the Unicode error

## General Use

    - Used for zrephrasing text from Markdown files to avoid Grammatical mistakes
    - Used to Build complete Docker COntainer 