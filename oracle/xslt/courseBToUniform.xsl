<?xml version="1.0" encoding="UTF-8"?>
<!-- B(Oracle) 课程格式 → 统一集成格式 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Classes>
      <xsl:for-each select="Classes/class">
        <class>
          <id><xsl:value-of select="id"/></id>
          <name><xsl:value-of select="name"/></name>
          <credit><xsl:value-of select="score"/></credit>
          <hours><xsl:value-of select="time"/></hours>
          <teacher><xsl:value-of select="teacher"/></teacher>
          <location><xsl:value-of select="location"/></location>
          <share_flag><xsl:value-of select="shareFlag"/></share_flag>
          <share_college>B</share_college>
        </class>
      </xsl:for-each>
    </Classes>
  </xsl:template>

</xsl:stylesheet>
