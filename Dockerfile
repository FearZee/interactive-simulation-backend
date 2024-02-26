FROM python:3.12
ENV PYTHONPATH "${PYTHONPATH}:/code/app"
ENV DATABASE_URI=

#
WORKDIR /code
ADD . .

#
COPY ./requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install psycopg2-binary
RUN pip install numpy

#
COPY . /code/app

#
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]