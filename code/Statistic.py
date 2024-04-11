# @file Statistic.py
#
# @brief Keep track of detected bee characteristics from collections import deque

class Statistics(object):
    """! The 'Statistics' class keeps track of all the monitoring results.
    """

    def __init__(self):
        """! Initializes the statistics object
        """
        self._beesIn = 0
        self._beesOut = 0
        self._beesInOverall = 0
        self._beesOutOverall = 0
        self._varroaCount = 0
        self._varroaCountOverall = 0
        self._processedFames = 0
        self._processedFamesOverlall = 0

    def frameProcessed(self):
        """! Increases the frame processed counter
        """
        self._processedFames += 1
        self._processedFamesOverlall += 1

    def addBeeIn(self):
        """! Increases the bee-in counter
        """
        self._beesIn += 1
        self._beesInOverall += 1

    def addBeeOut(self):
        """! Increases the bee-out counter
        """
        self._beesOut +=1
        self._beesOutOverall +=1

    def getBeeCountOverall(self):
        """! Returns the overal counted bees (bees_in, bees_out)
        @return tuple (bees_in, bees_out)
        """
        return (self._beesInOverall, self._beesOutOverall)

    def getBeeCount(self):
        """! Returns the counted bees (bees_in, bees_out)
        """
        return (self._beesIn, self._beesOut)

    def addDetection(self, tag):
        """! Adds a detected bee characteristic by tag
             @param tag
        """

        if "varroa" == tag:
            self._varroaCount += 1
            self._varroaCountOverall += 1

    def addClassificationResult(self, trackId, result):
        """! Adds a detected bee by classification results
             @param trackId unused
             @param result
        """
        if "varroa" in result:
            self.addDetection("varroa")

    def addClassificationResultByTag(self, trackId, tag):
        """! Adds a detected bee by tag
             @param trackId unused
             @param tag
        """
        self.addDetection(tag)

    def readStatistics(self):
        """! Return the current statistics for counted varroa, bees in, bees out and the amount of processed frames
             @return tuple
        """
        return (self._varroaCount,
                self._beesIn,
                self._beesOut,
                self._processedFames)

    def readOverallStatistics(self):
        """! Return the overall statistics for counted varroa, bees in, bees out and the amount of processed frames
             @return tuple
        """
        return (self._varroaCountOverall,
                self._beesInOverall,
                self._beesOutOverall,
                self._processedFamesOverall)

    def resetStatistics(self):
        """! Resets the current statistics
        """
        self._varroaCount = 0
        self._beesIn = 0
        self._beesOut = 0
        self._processedFames = 0


__dh = None
def getStatistics():
    """! Returns the statistics object
    @return The statistics instance
    """
    global __dh
    if __dh == None:
        __dh = Statistics()

    return __dh

