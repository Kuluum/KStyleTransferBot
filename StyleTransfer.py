from model import StyleTransferModel

class StyleTransfer:
    def __init__(self):
        self.num_steps = 80
        self.image_size = 120
        self.content_image = None
        self.style_image = None
        self.progress_lambda = None
        self.progress_message = None
        self.cancelled = False

    def run(self):
        model = StyleTransferModel()
        model.num_steps = self.num_steps
        model.image_size = self.image_size
        model.progress_lambda = lambda progress: self.progress_action(progress)
        model.should_terminate_lambda = lambda: self.cancelled
        output = model.transfer_style(self.content_image, self.style_image)

        return output

    def progress_action(self, progress):
        self.progress_lambda(progress, self.progress_message)