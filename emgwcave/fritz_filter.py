fritz_emgw_filter = {}

var = [
  {
    "$project": {
      "_id": 1,
      "candid": 1,
      "objectId": 1,
      "prv_candidates.jd": 1,
      "prv_candidates.magpsf": 1,
      "prv_candidates.fid": 1,
      "prv_candidates.isdiffpos": 1,
      "prv_candidates.diffmaglim": 1,
      "isdiffpos": "$candidate.isdiffpos",
      "m_now": "$candidate.magpsf",
      "m_app": "$candidate.magap",
      "t_now": "$candidate.jd",
      "fid_now": "$candidate.fid",
      "sgscore": "$candidate.sgscore1",
      "sgscore2": "$candidate.sgscore2",
      "sgscore3": "$candidate.sgscore3",
      "srmag": "$candidate.srmag1",
      "srmag2": "$candidate.srmag2",
      "srmag3": "$candidate.srmag3",
      "sgmag": "$candidate.sgmag1",
      "simag": "$candidate.simag1",
      "rbscore": "$candidate.rb",
      "drbscore": "$candidate.drb",
      "magnr": "$candidate.magnr",
      "distnr": "$candidate.distnr",
      "distpsnr1": "$candidate.distpsnr1",
      "distpsnr2": "$candidate.distpsnr2",
      "distpsnr3": "$candidate.distpsnr3",
      "scorr": "$candidate.scorr",
      "fwhm": "$candidate.fwhm",
      "elong": "$candidate.elong",
      "nbad": "$candidate.nbad",
      "chipsf": "$candidate.chipsf",
      "gal_lat": "$coordinates.b",
      "ssdistnr": "$candidate.ssdistnr",
      "ssmagnr": "$candidate.ssmagnr",
      "ssnamenr": "$candidate.ssnamenr",
      "t_start": "$candidate.jdstarthist",
      "age": {
        "$subtract": [
          "$candidate.jd",
          "$candidate.jdstarthist"
        ]
      },
      "psfminap": {
        "$subtract": [
          "$candidate.magpsf",
          "$candidate.magap"
        ]
      }
    }
  },
  {
    "$project": {
      "objectId": 1,
      "t_now": 1,
      "t_start": 1,
      "m_now": 1,
      "fid_now": 1,
      "sgscore": 1,
      "rbscore": 1,
      "drbscore": 1,
      "magnr": 1,
      "distnr": 1,
      "scorr": 1,
      "gal_lat": 1,
      "ssdistnr": 1,
      "ssnamenr": 1,
      "ssmagnr": 1,
      "age": 1,
      "nbad": 1,
      "fwhm": 1,
      "elong": 1,
      "psfminap": 1,
      "prv_candidates": 1,
      "latitude": {
        "$gte": [
          {
            "$abs": "$gal_lat"
          },
          4
        ]
      },
      "positivesubtraction": {
        "$in": [
          "$isdiffpos",
          [
            1,
            "1",
            "t",
            True
          ]
        ]
      },
      "real": {
        "$gt": [
          "$drbscore",
          0.3
        ]
      },
      "rock": {
        "$and": [
          {
            "$gte": [
              "$ssdistnr",
              0
            ]
          },
          {
            "$lt": [
              "$ssdistnr",
              10
            ]
          },
          {
            "$lt": [
              {
                "$abs": "$ssmagnr"
              },
              20
            ]
          }
        ]
      },
      "young": {
        "$lt": [
          "$age",
          10
        ]
      },
      "pointunderneath": {
        "$and": [
          {
            "$gt": [
              "$sgscore",
              0.76
            ]
          },
          {
            "$lt": [
              "$distpsnr1",
              2
            ]
          }
        ]
      },
      "brightstar": {
        "$or": [
          {
            "$and": [
              {
                "$lt": [
                  "$distpsnr1",
                  20
                ]
              },
              {
                "$lt": [
                  "$srmag",
                  15
                ]
              },
              {
                "$gt": [
                  "$srmag",
                  0
                ]
              },
              {
                "$gt": [
                  "$sgscore",
                  0.49
                ]
              }
            ]
          },
          {
            "$and": [
              {
                "$lt": [
                  "$distpsnr2",
                  20
                ]
              },
              {
                "$lt": [
                  "$srmag2",
                  15
                ]
              },
              {
                "$gt": [
                  "$srmag2",
                  0
                ]
              },
              {
                "$gt": [
                  "$sgscore2",
                  0.49
                ]
              }
            ]
          },
          {
            "$and": [
              {
                "$lt": [
                  "$distpsnr3",
                  20
                ]
              },
              {
                "$lt": [
                  "$srmag3",
                  15
                ]
              },
              {
                "$gt": [
                  "$srmag3",
                  0
                ]
              },
              {
                "$gt": [
                  "$sgscore3",
                  0.49
                ]
              }
            ]
          },
          {
            "$and": [
              {
                "$eq": [
                  "$sgscore",
                  0.5
                ]
              },
              {
                "$lt": [
                  "$distpsnr1",
                  0.5
                ]
              },
              {
                "$or": [
                  {
                    "$lt": [
                      "$sgmag",
                      17
                    ]
                  },
                  {
                    "$lt": [
                      "$srmag",
                      17
                    ]
                  },
                  {
                    "$lt": [
                      "$simag",
                      17
                    ]
                  }
                ]
              }
            ]
          }
        ]
      },
      "variablesource": {
        "$or": [
          {
            "$and": [
              {
                "$lt": [
                  "$distnr",
                  0.4
                ]
              },
              {
                "$lt": [
                  "$magnr",
                  19
                ]
              },
              {
                "$gt": [
                  "$age",
                  90
                ]
              }
            ]
          },
          {
            "$and": [
              {
                "$lt": [
                  "$distnr",
                  0.8
                ]
              },
              {
                "$lt": [
                  "$magnr",
                  17
                ]
              },
              {
                "$gt": [
                  "$age",
                  90
                ]
              }
            ]
          },
          {
            "$and": [
              {
                "$lt": [
                  "$distnr",
                  1.2
                ]
              },
              {
                "$lt": [
                  "$magnr",
                  15
                ]
              },
              {
                "$gt": [
                  "$age",
                  90
                ]
              }
            ]
          }
        ]
      },
      "stationary": {
        "$anyElementTrue": {
          "$map": {
            "input": "$prv_candidates",
            "as": "cand",
            "in": {
              "$and": [
                {
                  "$gt": [
                    {
                      "$abs": {
                        "$subtract": [
                          "$t_now",
                          "$$cand.jd"
                        ]
                      }
                    },
                    0.02
                  ]
                },
                {
                  "$lt": [
                    "$$cand.magpsf",
                    99
                  ]
                },
                {
                  "$in": [
                    "$$cand.isdiffpos",
                    [
                      1,
                      "1",
                      True,
                      "t"
                    ]
                  ]
                }
              ]
            }
          }
        }
      }
    }
  },
  {
    "$match": {
      "brightstar": False,
      "pointunderneath": False,
      "positivesubtraction": True,
      "real": True,
      "stationary": True,
      "variablesource": False,
      "young": True
    }
  },
]
