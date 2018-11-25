FROM python:3.7
COPY . /var/app
RUN pip install PyYAML
ENV APP_LOCALE_DIR=/var/locale
CMD ["python3", "/var/app/update-all-languages.py"]
