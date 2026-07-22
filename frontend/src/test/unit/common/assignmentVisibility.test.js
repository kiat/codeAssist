//import moment from "moment";
import {
  getPublishStatus,
  isAssignmentVisible,
  publishStatusOrder,
} from "../../../common/assignmentVisibility";

describe("assignmentVisibility", () => {
  const fixedNow = new Date("2026-07-16T20:00:00.000Z");

  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(fixedNow);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe("isAssignmentVisible", () => {
    it("returns false for an unpublished assignment", () => {
      const assignment = {
        published: false,
        published_date: null,
      };

      expect(isAssignmentVisible(assignment)).toBe(false);
    });

    it("returns false when the assignment is published but its release date is in the future", () => {
      const assignment = {
        published: true,
        published_date: "2026-07-17T20:00:00.000Z",
      };

      expect(isAssignmentVisible(assignment)).toBe(false);
    });

    it("returns true when the assignment is published and its release date has passed", () => {
      const assignment = {
        published: true,
        published_date: "2026-07-15T20:00:00.000Z",
      };

      expect(isAssignmentVisible(assignment)).toBe(true);
    });

    it("returns true when the assignment is published without a release date", () => {
      const assignment = {
        published: true,
        published_date: null,
      };

      expect(isAssignmentVisible(assignment)).toBe(true);
    });

    it("returns true when the release date is exactly the current time", () => {
      const assignment = {
        published: true,
        published_date: fixedNow.toISOString(),
      };

      expect(isAssignmentVisible(assignment)).toBe(true);
    });
  });

  describe("getPublishStatus", () => {
    it('returns "unpublished" when published is false', () => {
      const assignment = {
        published: false,
        published_date: null,
      };

      expect(getPublishStatus(assignment)).toBe("unpublished");
    });

    it('returns "scheduled" for a published assignment with a future release date', () => {
      const assignment = {
        published: true,
        published_date: "2026-07-17T20:00:00.000Z",
      };

      expect(getPublishStatus(assignment)).toBe("scheduled");
    });

    it('returns "published" for a published assignment with a past release date', () => {
      const assignment = {
        published: true,
        published_date: "2026-07-15T20:00:00.000Z",
      };

      expect(getPublishStatus(assignment)).toBe("published");
    });

    it('returns "published" for a published assignment without a release date', () => {
      const assignment = {
        published: true,
        published_date: null,
      };

      expect(getPublishStatus(assignment)).toBe("published");
    });

    it('returns "published" when the release date is exactly the current time', () => {
      const assignment = {
        published: true,
        published_date: fixedNow.toISOString(),
      };

      expect(getPublishStatus(assignment)).toBe("published");
    });
  });

  describe("publishStatusOrder", () => {
    it("orders unpublished, scheduled, and published statuses", () => {
      expect(publishStatusOrder.unpublished).toBeLessThan(
        publishStatusOrder.scheduled
      );
      expect(publishStatusOrder.scheduled).toBeLessThan(
        publishStatusOrder.published
      );
    });
  });
});