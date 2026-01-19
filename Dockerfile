# Используем официальный образ Python в качестве базового образа
FROM python
# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /usr/src/app
# Копируем файл requirements.txt внутрь контейнера
COPY requirements.txt ./
# Устанавливаем зависимости, описанные в файле requirements.txt
RUN apt-get update && apt-get install -y zsh
# Optional: Set Zsh as the default shell for the root user
RUN sh -c "$(wget https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"
RUN chsh -s /bin/zsh root

#give ARG RAILS_ENV a default value = production
ARG SYSTEME_DJANGO_MOD=DOCKER
ARG DJANGO_SETTINGS_MODULE=systeme
#assign the $SYSTEME_DJANGO_MOD arg to the SYSTEME_DJANGO_MOD ENV so that it can be accessed
#by the subsequent RUN call within the container
ENV SYSTEME_DJANGO_MOD $SYSTEME_DJANGO_MOD

RUN pip install -r requirements.txt

