# Simple home mass controller update
Утилита для массового обновления ПО Simple Home
## Настройка окружения
Python 3.12

Создание виртуального окружения:
```bash
python3 -m venv venv
source venv/bin/activate
```
Установка зависимостей:
```bash
pip install -r requirements.txt
```
## Конфигурация
### Пример конфигурации
```yaml
websockets:
  url: wss://dev.cloud.simple-home.liis.su
  login: login
  password: password

report_writer:
  report_dir_path: reports
  is_absolute_path: false
  detail_report: true

actions:
  validate:
    timeout: 10
    enabled: true
  update:
    timeout: 300
    enabled: true

software_build_url: https://files.liisteam.liis.su/api/public/.../simplehome.zip
file_service_token: access-token

max_pool_size: 10

controllers_whitelist:
 - wirenboard-QWERTY01
 - wirenboard-QWERTY02

controllers_blacklist:
 - wirenboard-QWERTY03
 - wirenboard-QWERTY04

controller_uid_regex: wirenboard-[A-Z0-9]{8}
```
### Описание синтаксиса

|Параметр|Тип данных|Обязательный|Значение по умолчанию|Описание|
| :--- | :---: | :---: | :---: | --- |
|`software_build_url`|`str`|✅||Ссылка на сборку ПО Simple Home|
|`file_service_token`|`str`|✅||Токен для доступа к API Fileservice-а|
|`max_pool_size`|`int`||10|Максимальное количество активных websocket соединений с облачным брокером|
|`controller_uid_regex`|`str`||None|Регулярное выражение, которое используется для фильтрации контроллеров по uid. К примеру, если необходимо обновить только контроллеры wirenboard, то это можно сделать применив выражение `wirenboard-[A-Z0-9]{8}`|
|`controllers_whitelist`|`list[str]`||[]|Список uid контроллеров, на которые необходимо установить обновление. Другие контроллеры не будут обновлены. Если определен, то `controllers_blacklist` игнорируется|
|`controllers_blacklist`|`list[str]`||[]|Список uid контроллеров, которые нужно игнорировать. Если определен `controllers_whitelist`, то данный параметр игнорируется|
|`websockets.url`|`str`||"wss://dev.cloud.simple-home.liis.su"|Домен брокера сообщений в формате `{ws, wss}://domain[:port]`|
|`websockets.login`|`str`|✅||Логин для подключения к брокеру|
|`websockets.password`|`str`|✅||Пароль для подключения к брокеру|
|`report_writer.report_dir_path`|`str`||Текущая рабочая директория|Папка для сохранения отчетов|
|`report_writer.is_absolute_path`|`bool`||true|Если true, то `report_writer.report_dir_path` рассматривается как путь относительно текущей рабочей директории. Иначе `report_writer.report_dir_path` рассматривается как абсолютный путь|
|`report_writer.detail_report`|`bool`||true|Если true, то вывод каждого контроллера будет записан в отдельный файл. Иначе выводы контроллеров не сохраняются в отчет|
|`actions.update`|`dict`|||Конфигурация метода обновления контроллеров|
|`actions.update.timeout`|`int`||300|Таймаут (в секундах), по истечении которого запрос на обновление контроллера считается провальным|
|`actions.update.enabled`|`bool`||true|Если false, то метод обновления не будет запущен|
|`actions.validate`|`dict`|||Конфигурация метода валидации контроллеров. Валидатор - это метод, который проверяет наличие на контроллере служебного сервиса (sh-updater). Если сервис не установлен, то валидатор исключает контроллер из выборки и данный контроллер не будет обновлен|
|`actions.validate.timeout`|`int`||10|Таймаут (в секундах), по истечении которого запрос версии ПО контроллера считается провальным|
|`actions.validate.enabled`|`bool`||true|Если false, то валидатор не будет запущен|
## Запуск
### Синтаксис команды
``` bash
python main.py -c CONFIGURATION_FILE [-y] [-u SOFTWARE_BUILD_URL]
```
### Описание синтаксиса
|Параметр|Принимаемое значение|Обязательный|Значение по умолчанию|Описание|
| :--- | :---: | :---: | :---: | --- |
|-c|Yaml файл с конфигурацией|✅||Принимает путь до yaml файла с конфигурацией|
|-y||||Если передан, то утилита не запрашивает подтверждение от пользователя|
|-u|Ссылка на сборку ПО Simple Home||Значение параметра `software_build_url` из файла конфигурации|Ссылка на сборку ПО Simple Home|
## Пример команды
``` bash
python main.py -c config.yaml -y -u https://files.liisteam.liis.su/api/public/.../simplehome.zip
```
