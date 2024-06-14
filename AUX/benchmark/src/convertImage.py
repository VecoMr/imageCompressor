from PIL import Image

def convertToHaskell(input, output, verbose=False):
    if verbose:
        print(f"Convert image [{input}] to haskell [{output}] started.")
    img = Image.open(input).convert("RGB")
    pixels = img.load()
    pixelsList = [((x, y), pixels[x, y]) for x in range(img.width) for y in range(img.height)]
    with open(output, "w") as file:
        for pixel in pixelsList:
            file.write(f"{str(pixel[0]).replace(' ','')} {str(pixel[1]).replace(' ','')}\n")
    if verbose:
        print(f"Convert image [{input}] to haskell [{output}] ended.")
