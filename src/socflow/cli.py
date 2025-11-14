import click

@click.group()
def main():
    """SocFlow is a unified data collection framework for Reddit, Bluesky, Mastodon, and News sources."""
    
@main.command()
def reddit():
    """Collect data from Reddit."""
    click.echo("Collecting data from Reddit...")

@main.command()
def bluesky():
    """Collect data from Bluesky."""
    click.echo("Collecting data from Bluesky...")

@main.command()
def mastodon():
    """Collect data from Mastodon."""
    click.echo("Collecting data from Mastodon...")

@main.command()
def news():
    """Collect data from News."""
    click.echo("Collecting data from News...")

if __name__ == "__main__":
    main()