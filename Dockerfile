# Используем официальный образ Python в качестве базового образа
FROM python
# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /usr/src/app
# Копируем файл requirements.txt внутрь контейнера
COPY requirements.txt ./
# Устанавливаем зависимости, описанные в файле requirements.txt
RUN apt-get update
#give ARG RAILS_ENV a default value = production
ARG SYSTEME_DJANGO_MOD=DOCKER
ARG DJANGO_SETTINGS_MODULE=systeme
#assign the $SYSTEME_DJANGO_MOD arg to the SYSTEME_DJANGO_MOD ENV so that it can be accessed
#by the subsequent RUN call within the container
ENV SYSTEME_DJANGO_MOD $SYSTEME_DJANGO_MOD

RUN pip install -r requirements.txt

