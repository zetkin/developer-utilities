FROM python:3.7
COPY . /var/app
RUN pip install -r /var/app/requirements.txt
ENV APP_LOCALE_DIR=/var/locale
CMD ["python3", "/var/app/update-all-languages.py"]
