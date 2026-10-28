"""SAMS application factory (presentation + application layers)."""
import os

from flask import Flask, render_template


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "sams.sqlite"),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    from . import auth, db, faculty, students

    db.init_app(app)
    for module in [auth, students, faculty]:
        app.register_blueprint(module.bp)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template(
            "error.html", code=403, message="You do not have permission to do that."
        ), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            "error.html", code=404, message="Page not found."
        ), 404

    return app
