<?xml version="1.0" encoding="UTF-8"?>
<!-- 课程过滤: 仅保留共享课程 (share_flag = 'Y') -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Classes>
      <xsl:for-each select="Classes/class[share_flag='Y']">
        <class>
          <id><xsl:value-of select="id"/></id>
          <name><xsl:value-of select="name"/></name>
          <credit><xsl:value-of select="credit"/></credit>
          <hours><xsl:value-of select="hours"/></hours>
          <teacher><xsl:value-of select="teacher"/></teacher>
          <location><xsl:value-of select="location"/></location>
          <share_flag><xsl:value-of select="share_flag"/></share_flag>
          <share_college><xsl:value-of select="share_college"/></share_college>
        </class>
      </xsl:for-each>
    </Classes>
  </xsl:template>

</xsl:stylesheet>
