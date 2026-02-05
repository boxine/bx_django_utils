

class MultiDBRouter:

    def _model_name_to_db(self, model_name: str):
        if 'secondary' in model_name.lower():
            return 'second'
        else:
            return 'default'

    def db_for_read(self, model, **hints):
        return self._model_name_to_db(model.__name__)

    def db_for_write(self, model, **hints):
        return self._model_name_to_db(model.__name__)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name:
            return self._model_name_to_db(model_name) == db
        else:
            return 'default'
