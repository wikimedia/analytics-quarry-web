from quarry.web.app import create_app

if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, host='0.0.0.0')
