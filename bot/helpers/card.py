class Card:
    edition_arr = [ "Normal","Foil","Holographic","Polychrome","Negative" ]
    quality_arr = [ "Poor", "Decent", "Good", "Great", "Mint"]


    def __init__(self, name: str, edition: int = -1, quality: int = -1, id: int = -1):
        if edition == -1:
            arr = name.split(",")
            self.name = arr[0]
            self.edition = int(arr[1])
            self.quality = int(arr[2])
            self.id = int(arr[3])
            return
        self.name = name
        self.edition = edition
        self.quality = quality
        self.id = id

    def compress(self):
        val = self.name + "," + str(self.edition) + "," + str(self.quality) + "," + str(self.id)
        return val

    def toString(self):
        return f"{self.edition_arr[self.edition]} {self.name}: {self.quality_arr[self.quality]} Quality, Edition {self.id}"