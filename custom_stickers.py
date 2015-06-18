"""Tools for keeping track of the custom Trello stickers used on our big board.

We use a few different custom sticker images to represent color states on the
big board (find 'em in /stickers/). These custom stickers need to be uplodaded
to a Trello account that has Trello gold enabled (which is the case for KA's
bigboard@khanacademy.org Trello role account).

TODO(kamens): in the future it'd be cool to have this app automatically upload
the custom stickers, but right now that's a manual step described in README.md.
"""


class CustomSticker(object):
    """Each CustomSticker represents one color of big board sticker."""
    def __init__(self, shortname, filename):
        self.shortname = shortname  # shortname of sticker, e.g. 'G' or 'P'
        self.filename = filename  # filename, e.g. 'green.png'

        # We need each custom sticker's trello id and image url to be able to
        # add new custom stickers to cards. We populate these properties on
        # demand and just leave 'em cached in memory.
        self.trello_id = None
        self.trello_image_url = None


class CustomStickers(object):
    """CustomStickers is an in-memory cache of all CustomSticker objects.

    This is used more as a namespace than a class - it's never instantiated."""

    # Class properties representing each color sticker
    Green = CustomSticker("G", "green.png")
    Purple = CustomSticker("P", "purple.png")
    Red = CustomSticker("R", "red.png")
    Yellow = CustomSticker("Y", "yellow.png")
    White = CustomSticker("W", "white.png")

    # Class property that keeps track of whether or not we've grabbed Trello's
    # properties for each custom sticker
    has_populated_trello_properties = False

    @classmethod
    def all(cls):
        """Return all custom stickers."""
        return [
                CustomStickers.Green,
                CustomStickers.Purple,
                CustomStickers.Red,
                CustomStickers.Yellow,
                CustomStickers.White,
                ]

    @classmethod
    def from_shortname(cls, shortname):
        """Return custom sticker with matching shortname (e.g. 'R' or 'G')"""
        for custom_sticker in cls.all():
            if custom_sticker.shortname == shortname:
                return custom_sticker
        return None

    @classmethod
    def from_trello_image_url(cls, trello_image_url):
        """Return custom sticker with filename matching supplied trello URL."""
        for custom_sticker in cls.all():
            if trello_image_url.endswith(custom_sticker.filename):
                return custom_sticker
        return None

    @classmethod
    def populate_trello_properties(cls, client):
        """Populate the trello-specific properties on our in-memory stickers.

        This hits Trello's API, grabs all custom stickers, and inflates the
        Trello id and Trello URL properties for all the big board custom
        stickers."""
        if cls.has_populated_trello_properties:
            return

        trello_custom_stickers = client.me.customStickers
        expected_custom_stickers = CustomStickers.all()

        for trello_sticker in trello_custom_stickers:
            for expected_sticker in expected_custom_stickers:
                if trello_sticker.url.endswith(expected_sticker.filename):
                    expected_sticker.trello_image_url = trello_sticker.url
                    expected_sticker.trello_id = trello_sticker._id

        # Assert that we found Trello custom stickers for all expected big
        # board sticker colors
        for expected_sticker in expected_custom_stickers:
            if (not expected_sticker.trello_id or
                    not expected_sticker.trello_image_url):
                raise Exception("Unable to populate trello properties for all"
                                "expected custom stickers.")

        cls.has_populated_trello_properties = True
