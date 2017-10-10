# Unique face object
class Face:

    def __init__(self, uuid, name, embeddings, samples):
        self.uuid = uuid
        self.name = name
        self.embeddings = embeddings
        self.samples = samples

    def __hash__(self):
        return hash(self.uuid)

    def __eq__(self, other):
        return self.uuid == other.uuid

    def setName(self, name):
        self.name = name

    def setEmbeddings(self, embeddings):
        self.embeddings = embeddings

    def setSamples(self, samples):
        self.samples = samples

    def __repr__(self):
        return "{{uuid: {}, name: {}, embeddings[0:5]: {}, samples: {}}}".format(
            self.uuid,
            self.name,
            self.embeddings[0:5],
            self.samples)

# Unique face object for drawing
class VizFace(Face):

    def __init__(self, uuid, name, embeddings, samples, color, color_hex):
        Face.__init__(self, uuid, name, embeddings, samples)
        self.color = color
        self.color_hex = color_hex

    def __repr__(self):
        return "{{uuid: {}, name: {}, color: {}, embeddings[0:5]: {}, samples: {}}}".format(
            self.uuid,
            self.name,
            '#' + self.color_hex,
            self.embeddings[0:5],
            self.samples)
