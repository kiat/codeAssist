// request success port
export const SUCCESS = {
  status: 1,
  message: "request succeed",
};

// request fail port
export const FAIL = {
  status: 0,
  message: "request failed",
};

// course port
export const COURSES = [
  {
    semester: "Fall 2022",
    courses: [
      {
        code: "T21",
        name: "TEST 21",
        assignmentCount: 5,
        id: 21,
      },
      {
        code: "T22",
        name: "TEST 22",
        assignmentCount: 5,
        id: 22,
      },
      {
        code: "T23",
        name: "TEST 23",
        assignmentCount: 5,
        id: 23,
      },
    ],
  },
  {
    semester: "Spring 2022",
    courses: [
      {
        code: "T11",
        name: "TEST 11",
        assignmentCount: 14,
        id: 11,
      },
      {
        code: "T12",
        name: "TEST 11",
        assignmentCount: 17,
        id: 12,
      },
    ],
  },
];

// assignment port
export const COURSE = {
  id: 54321,
  code: "T S 22",
  name: "Su22-ELEMENTS OF SOFTWARE DESIGN-WB(86439)",
  semester: "Summer 2022",
  assignments: [
    {
      name: "Training-test-11",
      status: 0,
      released: 1658362328000,
      due: 1671581528000,
      id: 1,
    },
    {
      name: "Training-test-12",
      status: 1,
      released: 1661055128000,
      due: 1663733528000,
      id: 2,
    },
    {
      name: "Training-test-13",
      status: 1,
      released: 1658362328000,
      due: 1671581528000,
      id: 3,
    },
    {
      name: "Training-test-14",
      status: 0,
      released: 1661055128000,
      due: 1663733528000,
      id: 4,
    },
    {
      name: "Training-test-15",
      status: 1,
      released: 1661055128000,
      due: 1671581528000,
      id: 5,
    },
    {
      name: "Training-test-16",
      status: 0,
      released: 1661055128000,
      due: 1663733528000,
      id: 6,
    },
    {
      name: "Training-test-17",
      status: 0,
      released: 1661055128000,
      due: 1663733528000,
      id: 7,
    },
    {
      name: "Training-test-18",
      status: 0,
      released: 1661055128000,
      due: 1663733528000,
      id: 8,
    },
    {
      name: "Training-test-19",
      status: 0,
      released: 1661055128000,
      due: 1663733528000,
      id: 9,
    },
    {
      name: "Training-test-20",
      status: 0,
      released: 1661055128000,
      due: 1663733528000,
      id: 10,
    },
    {
      name: "Training-test-21",
      status: 0,
      released: 1661055128000,
      due: 1663733528000,
      id: 11,
    },
    {
      name: "Training-test-22",
      status: 0,
      released: 1661055128000,
      due: 1663733528000,
      id: 12,
    },
  ],
};

// assignment result port
export const ASSIGNMENTRESULT = {
  assignmentName: "A123",
  score: "2.0/2.0",
  released: 1658362328000,
  due: 1671581528000,
  results: [
    {
      name: "test(tester.TestDiffs) (30.0/30.0)",
      passed: "1",
      text: "test text",
      id: 1,
    },
    {
      name: "test_slow(tester.TestDiffs) (30.0/30.0)",
      passed: "1",
      text: "test text2",
      id: 2,
    },
    {
      name: "test_collision(tester2.TestDiffs) (5.0/5.0)",
      passed: "1",
      text: "test text3",
      id: 3,
    },
  ],
  codes: [
    {
      id: 1,
      name: "TopoSort.py",
      text: "code 1",
    },
    {
      id: 2,
      name: "TopoSort2.py",
      text: "code 2",
    },
  ],
};

// assignment submission history port
export const SUBMISSIONHISTORY = [
  {
    id: "2",
    order: "2",
    cdt: "Sep 29 at 11:02PM",
    submitters: "3",
    score: "100",
    active: "1",
  },
  {
    id: "1",
    order: "1",
    cdt: "Sep 29 at 10:24PM",
    submitters: "2",
    score: "90",
    active: "0",
  },
];
