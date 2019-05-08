# Alexa-Ferry-Skill

This is the soure code repository for my 2019 Computer Science Senior Thesis project at Willamette University. For my project I solicited and organized past Washington State Ferry departure data and other sources of information. The information was fed through an Amazon Alexa skill that provides future departure predictions and other helpful information for ferry riders.

In this README I _try_ to be succinct while including more information in the [Wiki Page](https://github.com/imkacarlson/Alexa-Ferry-Skill/wiki) for this repository.

 ![image](https://raw.githubusercontent.com/imkacarlson/Alexa-Ferry-Skill/master/docs/images/Ferry.JPG)

 # Overview
 When I started this project I had many different tools in mind that I wanted to use. The code I wrote in exploring these tools is included here but, ultimately, I ended up doing most everything with Amazon Web Services.

All Jupyter Notebooks were run through [Anaconda](https://www.anaconda.com/) with Python 3.6.2.

 # Important things to keep in mind
  - In most of the files that interface with Amazon Web Services my bucket name is not included. I usually have a variable called `bucket_name` or something that in this public repository is redacted to just '`#####`'. If trying to replicate you will need to fill this in with your bucket name.

 # Order of reading

 # Breif description of directories
directory                         |  description                                                               | dependencies
----------------------------------|----------------------------------------------------------------------------|----------------
ARIMA                             |  Contains a Jupyter Notebook with code I used to try and fit an ARIMA model to my data. This was never used in the final product.                | 'pandas', 'matplotlib', ['statsmodels'](https://www.statsmodels.org/devel/index.html)  
AWS-Sagemaker                     |  Contains Jupyter Notebooks that were run in the cloud on [AWS SageMaker](https://aws.amazon.com/sagemaker/). See my AWS-SageMaker [wiki page](https://github.com/imkacarlson/Alexa-Ferry-Skill/wiki/AWS-Sagemaker) for more information on each notebook.     |[AWS SageMaker](https://aws.amazon.com/sagemaker/)
Exploratory-Data-Analysis         |  Contains Jupyter Notebooks that I ran locally on my PC to start getting a feel for the data I had recieved from WSDOT. See the [wiki page]() for more info. | 'pandas', 'numpy'

 # How to replicate what I have done

 # How it fits together into the Alexa Skill