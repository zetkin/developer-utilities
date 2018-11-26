FROM python:3.7
RUN pip install PyYAML
COPY . /var/app
ENV APP_LOCALE_DIR=/var/locale
CMD ["python3", "/var/app/update-all-languages.py"]
