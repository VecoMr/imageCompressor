{-
-- EPITECH PROJECT, 2024
-- imageCompressor
-- File description:
-- Lib
-}

module Main (main) where

import System.Environment (getArgs)
import Data.Maybe (mapMaybe)
import System.Random (randomRIO)
import Text.Printf (printf)
import System.IO (hSetBuffering, stdout, BufferMode(..))

data Options = Options {
    numberOfColors::Int,
    convergenceLimit::Float,
    filePath::FilePath
} deriving (Show)

parseArgs :: [String] -> Maybe Options
parseArgs ["-n", n, "-l", l, "-f", f] = Just $ Options (read n) (read l) f
parseArgs _ = Nothing

data Point = Point { xCoord :: Int, yCoord :: Int }

instance Show Point where
    show (Point x y) = show (x,y)

creerPoint :: Int -> Int -> Point
creerPoint x y = Point { xCoord = x, yCoord = y }

data Couleur = Couleur { rouge :: Int, vert :: Int, bleu :: Int } deriving (Eq)

instance Show Couleur where
    show (Couleur r g b) = show (r,g,b)

data Pixel = Pixel { point::Point, color::Couleur }

instance Show Pixel where
    show (Pixel p c) = printf "%s %s" (show p) (show c)

creerCouleur :: Int -> Int -> Int -> Maybe Couleur
creerCouleur r g b
    | r >= 0 && r <= 255 &&
      g >= 0 && g <= 255 &&
      b >= 0 && b <= 255 = Just (Couleur r g b)
    | otherwise = Nothing

parseLigne :: String -> Maybe Pixel
parseLigne ligne = case words ligne of
    [pointStr, couleurStr] -> do
        point <- parsePoint pointStr
        couleur <- parseCouleur couleurStr
        return Pixel { point = point, color = couleur }
    _ -> Nothing

parsePoint :: String -> Maybe Point
parsePoint str = case reads str of
    [(x, ',':y)] -> Just (Point x (read y))
    _ -> Nothing

parseCouleur :: String -> Maybe Couleur
parseCouleur str = case reads str of
    [(r, ',':gs)] -> do
        let (g', ',':b') = break (== ',') gs
        couleur <- creerCouleur r (read g') (read b')
        return couleur
    _ -> Nothing

data Centroid = Centroid {
    couleur::Couleur,
    points::[Pixel]
}

instance Eq Centroid where
    (Centroid c1 _) == (Centroid c2 _) = c1 == c2

instance Show Centroid where
    show (Centroid c ps) = printf "--\n%s\n-\n" (show c) ++ putsPixel ps

randomColor :: IO Couleur
randomColor = do
    r <- randomRIO (0, 255)
    g <- randomRIO (0, 255)
    b <- randomRIO (0, 255)
    return $ Couleur r g b

initializeClusters :: Int -> IO [Centroid]
initializeClusters 0 = return []
initializeClusters n = do
    color <- randomColor
    rest <- initializeClusters (n - 1)
    return ((Centroid color []) : rest)

distance :: Couleur -> Couleur -> Float
distance (Couleur r1 g1 b1) (Couleur r2 g2 b2) = sqrt $ fromIntegral ((r1 - r2) ^ 2 + (g1 - g2) ^ 2 + (b1 - b2) ^ 2)

isNearest :: Centroid -> Pixel -> [Centroid] -> Bool
isNearest c p cs = distance (couleur c) (color p) == minimum (map (\c' -> distance (couleur c') (color p)) cs)

nearestPixelToCentroid :: Centroid -> [Pixel] -> [Centroid] -> [Pixel]
nearestPixelToCentroid _ [] _ = []
nearestPixelToCentroid c (x:xs) cs = if isNearest c x cs
    then x : nearestPixelToCentroid c xs cs else nearestPixelToCentroid c xs cs

nextStep :: [Centroid] -> [Pixel] -> [Centroid]
nextStep cs p = map updateCentroidPoints cs
    where
        updateCentroidPoints :: Centroid -> Centroid
        updateCentroidPoints c = Centroid {couleur = (couleur c), points = nearestPixelToCentroid c p cs}

updateColor :: [Centroid] -> [Centroid]
updateColor [] = []
updateColor (c:cs) = Centroid (findNextColor (couleur c) (map color (points c))) (points c) : updateColor cs

findNextColor :: Couleur -> [Couleur] -> Couleur
findNextColor c [] = c
findNextColor _ cs = Couleur (sum (map rouge cs) `div` length cs) (sum (map vert cs) `div` length cs) (sum (map bleu cs) `div` length cs)

putsPixel :: [Pixel] -> String
putsPixel = concatMap (\p -> show p ++ "\n")

putsCentroid :: [Centroid] -> IO ()
putsCentroid = mapM_ print

main :: IO ()
main = do
    hSetBuffering stdout (BlockBuffering (Just 8192))
    args <- getArgs
    case parseArgs args of
        Just options -> do
            -- putStrLn $ "Number of colors: " ++ show (numberOfColors options)
            -- putStrLn $ "Convergence limit: " ++ show (convergenceLimit options)
            -- putStrLn $ "File path: " ++ filePath options
            contenu <- readFile (filePath options)
            let lignes = map (filter (`notElem` "()")) (lines contenu)
                image = mapMaybe parseLigne lignes
            initialClusters <- initializeClusters (numberOfColors options)
            let next = nextStep initialClusters image
            putsCentroid $ updateColor $ nextStep (updateColor $ nextStep (updateColor $ nextStep (updateColor next) image) image) image
        Nothing -> putStrLn "USAGE: ./imageCompressor -n N -l L -f F"
