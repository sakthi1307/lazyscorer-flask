# LzyScorer

This is a Flask app that uses MongoDB as a backend database and Google Cloud Vision API for image recognition.

## Installation

To install the required dependencies, run the following command:

```
pip install -r requirements.txt
```

You will also need to install MongoDB on your machine. Please follow the instructions on the [official MongoDB website](https://www.mongodb.com/) to install it.



## MongoDB Setup

To use MongoDB with this app, you will need to set the following environment variables:

- `MONGO_USERNAME`: Your MongoDB username.
- `MONGO_PASSWORD`: Your MongoDB password.
- `MONGO_URL`: The URL of your MongoDB instance.

You can set these variables by running the following commands in your terminal:

```
export MONGO_USERNAME=<your_username>
export MONGO_PASSWORD=<your_password>
export MONGO_URL=<your_mongodb_url>
```

Alternatively, you can create a `.env` file in the root directory of the project and set the variables there. Be sure to add the `.env` file to your `.gitignore` file to prevent it from being committed to your repository.

## Google Cloud Vision Setup

To use Google Cloud Vision with this app, you will need to set the following environment variables:

- `GOOGLE_APPLICATION_CREDENTIALS`: The location of your Google Cloud Vision API key (JSON file).

You can set this variable by running the following command in your terminal:

```
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json
```


## Usage

To run the app, use the following command:
```
python app.py
```
Once the app is running, you can access it by navigating to `http://localhost:5000` in your web browser.

## License

This app is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

