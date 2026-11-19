"""Flask CLI commands for server operators."""
import click

VALID_ROLES = ("admin", "instructor", "student")


def register_cli(app):
    @app.cli.command("set-role")
    @click.argument("email")
    @click.argument("role", type=click.Choice(VALID_ROLES))
    def set_role(email, role):
        """Set the global role of the account with EMAIL.

        Public sign-up only creates students, so use this to create the first
        admin on a new server. After that, admins manage roles in the admin panel:

            flask set-role you@example.com admin
        """
        from api import db
        from api.models import User

        user = db.session.query(User).filter_by(email_address=email).first()
        if user is None:
            raise click.ClickException(f"No account with email {email}. Sign up first, then rerun this.")
        old_role = user.role
        user.role = role
        db.session.commit()
        click.echo(f"{email}: {old_role} -> {role}")
