import argparse
from PIL import Image

def convertImageHaskell(input, output):
    print(f"Convert image [{input}] to haskell [{output}]")
    img = Image.open(input).convert("RGB")
    pixels = img.load()
    pixelsList = [((x, y), pixels[x, y]) for x in range(img.width) for y in range(img.height)]
    with open(output, "w") as file:
        for pixel in pixelsList:
            file.write(f"{str(pixel[0]).replace(' ','')} {str(pixel[1]).replace(' ','')}\n")


def convertImageImage(input, output, verbose=False):
    if verbose:
        print(f"Convert image [{input}] to image [{output}]")
    pixelsList = []
    height = 0
    width = 0
    cluster = 0
    with open(input, "r") as file:
        pixels = file.readlines()
        pixels.pop(0)
        cluster += 1
        if verbose:
            print(f"CLUSTER: {cluster}")
        while pixels:
            cluster = tuple(map(int, pixels.pop(0)[1:-2].split(",")))
            pixels.pop(0)
            tmp = pixels.pop(0)
            while tmp != "--\n":
                if tmp == "\n":
                    if pixels:
                        tmp = pixels.pop(0)
                        continue
                    else:
                        break

                pos, _ = tmp.split(") (")
                x, y = map(int, pos[1:].split(','))
                pixelsList.append(((x, y), cluster))
                if x > width:
                    width = x
                if y > height:
                    height = y
                if pixels:
                    tmp = pixels.pop(0)
                else:
                    break
    print(f"Image size: {width+1}x{height+1}")
    img = Image.new("RGB", (width + 1, height + 1))
    pixels = img.load()
    for pixel in pixelsList:
        pixels[pixel[0]] = pixel[1]
    img.save(output)


def main():
    parser = argparse.ArgumentParser(description="Un exemple de script argparse.")
    parser.add_argument('-I', '--input', help='File to open', required=True)
    parser.add_argument('-O', '--output', help='File to output', required=True)
    parser.add_argument('-M', '--mode', help='mode to [haskell, image] format', required=True, choices=['haskell', 'image'])
    parser.add_argument('-V', '--verbose', help='verbose mode', action='store_true')
    args = parser.parse_args()
    if args.mode == "haskell":
        convertImageHaskell(args.input, args.output)
    else:
        convertImageImage(args.input, args.output, verbose=args.verbose)


if __name__ == "__main__":
    main()
