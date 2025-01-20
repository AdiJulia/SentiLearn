# routes/__init__.py
from .dashboard import dashboard_bp #from . memanggil nama dari routesnya
from .import_data import import_data_bp
from .preprocessing import preprocessing_bp 
from .klasifikasi import klasifikasi_bp
from .feature_extraction import feature_extraction_bp
from .datatraining import datatraining_bp 
from .datatesting import datatesting_bp 
from .traintest import traintest_bp 
from .testresult import testresult_bp 
from .register import register_bp 
from .login import login_bp 
from .admin_routes import admin_bp

def register_blueprints(app):
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(import_data_bp)
    app.register_blueprint(preprocessing_bp)
    app.register_blueprint(feature_extraction_bp)
    app.register_blueprint(klasifikasi_bp)
    app.register_blueprint(datatraining_bp)
    app.register_blueprint(datatesting_bp)
    app.register_blueprint(traintest_bp)
    app.register_blueprint(testresult_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(admin_bp)

